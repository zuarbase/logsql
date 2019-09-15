import multiprocessing

from addict import Dict

from logsql import client, models, utils
from logsql.offsetfile import OffsetFile

from .logger import Logger

PATH = "/tmp/test.log"


def test_client(logger, session):
    logger.print("line1")
    logger.print("line2")

    args = Dict()
    args.id = logger.container.id
    args.interval = 1.0
    args.run_once = True

    process = multiprocessing.Process(target=client.main, args=(args,),)
    process.start()
    process.join()

    logs = [log.as_dict() for log in session.query(models.Log).all()]
    assert len(logs) == 2
    for log in logs:
        assert log["id"]
        assert log["created_at"]
        assert log["json"]["stream"] == "stderr"
    assert logs[0]["json"]["log"] == "line1\n"
    assert logs[1]["json"]["log"] == "line2\n"


def test_client_reset(logger, session):
    logger.print("line1")
    logger.print("line2")

    args = Dict()
    args.id = logger.container.id
    args.interval = 1.0
    args.reset = True
    args.run_once = True

    offsetfile = OffsetFile(logger.logpath)
    offsetfile.inode = utils.inode_number(logger.logpath)
    offsetfile.offset = 128
    offsetfile.save()

    log_path = client.main(args)
    assert log_path.count == 2


def test_client_long_name(docker_client, session):

    logger = Logger(docker_client, name="X" * 256)
    try:
        logger.print("line1")
        args = Dict({
            "id": logger.container.id,
            "interval": 1,
            "debug": True,
            "run_once": True,
        })

        process = multiprocessing.Process(target=client.main, args=(args,),)
        process.start()
        process.join()

        logs = [log.as_dict() for log in session.query(models.Log).all()]
        assert logs[0]["container_name"] == "/" + ("X" * 127)
    finally:
        logger.container.kill()


def test_client_transform(logger, session, mocker):

    def _side_effect(container_name, data):
        if data["log"] == "line2\n":
            return data
        return None

    mocked = mocker.patch.object(client, "transform")
    mocked.side_effect = _side_effect

    logger.print("line1")
    logger.print("line2")

    args = Dict()
    args.id = logger.container.id
    args.interval = 1.0
    args.run_once = True

    process = multiprocessing.Process(target=client.main, args=(args,),)
    process.start()
    process.join()

    logs = [log.as_dict() for log in session.query(models.Log).all()]
    assert len(logs) == 1
    assert logs[0]["json"]["log"] == "line2\n"


def test_client_batch_size(logger, session):
    logger.print("line1")
    logger.print("line2")
    logger.print("line3")

    args = Dict({
        "id": logger.container.id,
        "interval": 1,
        "debug": True,
        "run_once": True,
        "batch_size": 2
    })

    process = multiprocessing.Process(target=client.main, args=(args,),)
    process.start()
    process.join()

    logs = [log.as_dict() for log in session.query(models.Log).all()]
    assert len(logs) == 2
    assert logs[0]["json"]["log"] == "line1\n"
    assert logs[1]["json"]["log"] == "line2\n"
