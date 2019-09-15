"""
This module is the entry point for per-log-file handling.
"""
import os
import sys
import argparse
import time
import logging
import json

import docker
import sqlalchemy
from sqlalchemy.pool import NullPool

from logsql import models, settings, utils
from logsql.logpath import LogPath
from logsql.offsetfile import OffsetFile
from logsql.transform import transform

DEFAULT_BATCH_SIZE = 10000


def main(
        args: dict
):
    """ The main entry point for the child subprocess that is run for a
    given log file
    """

    client = docker.from_env()
    info = client.api.inspect_container(args.id)
    run_once = getattr(args, "run_once", False)

    batch_size = getattr(args, "batch_size")
    if not batch_size:
        batch_size = DEFAULT_BATCH_SIZE

    done = False

    name = info["Name"]
    if len(name) > 128:
        name = name[0:128]

    logging.basicConfig(
        format="%(levelname)s:" + name + ":%(message)s",
        level=args.debug and logging.DEBUG or logging.INFO,
    )

    path = info["LogPath"]
    logging.info("%s started: %s", args.id, path)

    if args.reset:
        offset_file_path = info["LogPath"] + OffsetFile.DEFAULT_SUFFIX
        if os.path.exists(offset_file_path):
            logging.warning("Removing offsetfile: %s", offset_file_path)
            os.remove(offset_file_path)

    engine = sqlalchemy.create_engine(
        settings.DATABASE_URL, poolclass=NullPool
    )
    models.Session.configure(bind=engine)
    session = models.Session()

    utils.containers_chown(path)

    log_path = LogPath(path)
    while not done:
        lines = []
        while True:
            line = None
            try:
                line = log_path.readline()
            except FileNotFoundError:
                logging.info("FileNotFound %s, container likely removed", path)
                done = True
            if not line:
                break

            # assumes json formatting
            data = transform(info["Name"], json.loads(line))
            if not data:
                continue

            lines.append(data)
            logging.debug("LINE: %s", str(data))

            if len(lines) >= batch_size:
                break

        if not lines:
            if run_once:
                return log_path  # pragma: no coverage
            logging.debug("sleep")
            time.sleep(args.interval)
            continue

        logs = []

        for data in lines:
            log = models.Log(
                container_id=args.id, container_name=name, json=data
            )
            session.add(log)
            logs.append(log)
        session.commit()

        if args.debug:
            for log in logs:
                # careful, this can hang during same-process tests
                session.refresh(log)
                logging.debug("LOG: %s", log.as_dict())

        log_path.commit()

        if run_once:
            return log_path

    return 0


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("id")
    PARSER.add_argument("--debug", action="store_true", default=False)
    PARSER.add_argument("--interval", default=1.0)
    PARSER.add_argument("--reset", action="store_true", default=False)
    PARSER.add_argument("--batch-size", default=DEFAULT_BATCH_SIZE)

    sys.exit(main(PARSER.parse_args()))
