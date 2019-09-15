""" Parent application module """
import os
import sys
import threading
import subprocess
import logging
import time
import argparse
import signal

import docker
from docker.models.containers import Container
import sqlalchemy


from . import client, settings, models
from .offsetfile import OffsetFile


def sigterm_handler(signo, _stack_frame):
    """ SIGTERM signal handler """
    logging.info("SIGTERM received")
    sys.exit(128 + signo)


class Monitor:
    """ Monitor of all containers on the system. """

    def __init__(self, debug=False):
        self.debug = debug

        self.docker_client = docker.from_env()
        self.clients = {}

        self.quit = False

    def add_container(self, container_id: str):
        """ Add a container with the given id by staring a client process. """
        cmd = [sys.executable, client.__file__, container_id]
        if self.debug:
            cmd.append("--debug")

        process = subprocess.Popen(cmd)
        logging.info(
            "Starting monitoring process PID %d for container %s",
            process.pid, container_id
        )

        self.clients[container_id] = process

    def event_handler(self):
        """ Process docker events """
        for event in self.docker_client.events(decode=True):
            if self.quit:
                logging.info("monitor quitting.")
                return
            logging.debug("%s", str(event))
            event_type = event.get("Type", "").lower()
            if event_type == "container":
                action = event.get("Action", "").lower()
                if action == "start":
                    name = event["Actor"]["Attributes"]["name"]
                    if "logsql" not in name.lower():
                        self.add_container(event["id"])

    def inspect(self, container_id):
        """ Shortcut to low-level inspect_container"""
        return self.docker_client.api.inspect_container(container_id)

    def reset(self):
        """ Remove all offset files """
        for container in self.docker_client.containers.list(all=True):
            info = self.inspect(container.id)
            path = info["LogPath"] + OffsetFile.DEFAULT_SUFFIX
            if os.path.exists(path):
                logging.warning("Removing offsetfile: %s", path)
                os.remove(path)


def _should_add_container(
        monitor: Monitor,
        container: Container,
        level=logging.DEBUG,
) -> bool:
    if "logsql" in container.name.lower():
        logging.log(
            level,
            "Skipping container %s [%s]",
            container.name, container.id
        )
        return False
    info = monitor.inspect(container.id)
    if not info["LogPath"]:
        logging.warning(
            "Container %s [%s] has no LogPath, skipping",
            container.name, container.id
        )
        return False
    return True


def main(args):
    """ Main application entrypoint """
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level)

    monitor = Monitor()
    monitor.debug = args.debug

    engine = sqlalchemy.create_engine(
        settings.DATABASE_URL, poolclass=sqlalchemy.pool.NullPool
    )
    models.BASE.metadata.create_all(bind=engine)

    signal.signal(signal.SIGTERM, sigterm_handler)

    try:
        thread = threading.Thread(target=monitor.event_handler)
        thread.daemon = True
        thread.start()

        for container in monitor.docker_client.containers.list(all=True):
            if container.id not in monitor.clients:
                if _should_add_container(
                        monitor, container, level=logging.INFO
                ):
                    logging.info(
                        "Add container %s [%s]",
                        container.name, container.id
                    )
                    monitor.add_container(container.id)

        while True:
            logging.debug("sleeping main thread")
            time.sleep(args.interval)

            containers = monitor.docker_client.containers.list(all=True)
            for container in containers:
                if container.id not in monitor.clients:
                    if _should_add_container(monitor, container):
                        logging.warning(
                            "Manually adding container %s [%s]",
                            container.name, container.id
                        )
                        monitor.add_container(container.id)

            for container_id, process in monitor.clients.items():
                if process.poll() is None:
                    logging.debug(
                        "Process %s is still running", str(container_id)
                    )
                    continue

    except SystemExit:
        logging.info("SIGTERM, exiting ...")
        monitor.quit = True
        return 128 + signal.SIGTERM


def init():
    """ Module initialization """
    if __name__ == "__main__":
        parser = argparse.ArgumentParser()
        parser.add_argument("--debug", action="store_true", default=False)
        parser.add_argument("--interval", default=60.0)
        sys.exit(main(parser.parse_args()))


init()
