import os
import multiprocessing
import threading
import signal
import time

from addict import Dict

from logsql import models, __main__
from logsql.offsetfile import OffsetFile
from logsql.__main__ import main, Monitor
from .logger import Logger


def _wait_for_offsetfile(path):
    if not path.endswith(OffsetFile.DEFAULT_SUFFIX):
        path += OffsetFile.DEFAULT_SUFFIX
    for _ in range(100):
        if os.path.exists(path):
            return
        time.sleep(.1)
    assert os.path.exists(path)


def test_main(session, logger):
    args = Dict({
        "debug": False,
        "interval": 60
    })

    process = multiprocessing.Process(target=main, args=(args,),)
    try:
        process.start()

        logger.print("hello world")
        _wait_for_offsetfile(logger.logpath)

        logs = session.query(models.Log).all()
        assert len(logs) == 1
    finally:
        os.kill(process.pid, signal.SIGTERM)
        process.join()


def test_main_debug(session, logger):
    args = Dict({
        "debug": True,
        "interval": 60
    })

    process = multiprocessing.Process(target=main, args=(args,),)
    try:
        process.start()

        logger.print("hello again")
        _wait_for_offsetfile(logger.logpath)

        logs = session.query(models.Log).all()
        assert len(logs) == 1
    finally:
        os.kill(process.pid, signal.SIGTERM)
        process.join()


def test_main_quit(session, mocker):
    args = Dict({
        "debug": False,
        "interval": 60
    })
    mocked = mocker.patch("time.sleep")
    mocked.side_effect = SystemExit()
    assert main(args) == 128 + signal.SIGTERM


def test_main_event_handler(docker_client, session, mocker):
    monitor = Monitor()

    def _side_effect(*args, **kwargs):
        monitor.quit = True

    mocker.patch.object(monitor, "add_container", side_effect=_side_effect)

    thread = threading.Thread(target=monitor.event_handler)
    thread.start()

    logger = Logger(docker_client)
    try:
        logger.container.pause()  # ensure one more event
        thread.join()
    finally:
        logger.container.kill()


def test_main_monitor_reset(docker_client, session):
    monitor = Monitor()
    thread = threading.Thread(target=monitor.event_handler)
    thread.start()

    logger = Logger(docker_client)
    try:
        logger.print("hello again")
        _wait_for_offsetfile(logger.logpath)
        monitor.quit = True
        logger.container.pause()  # ensure one more event
        thread.join()
        monitor.reset()
    finally:
        logger.container.kill()


def test_main_logsql(docker_client, session, mocker):
    args = Dict({
        "debug": False,
        "interval": 60
    })

    def _side_effect(message, *args, **kwargs):
        if message == "sleeping main thread":
            raise SystemExit()

    mocked_debug = mocker.patch("logging.debug")
    mocked_debug.side_effect = _side_effect

    mocked_add_container = mocker.patch("logsql.__main__.Monitor.add_container")

    logger = Logger(docker_client, name="logsql")
    try:
        main(args)
    finally:
        logger.container.kill()

    mocked_add_container.assert_not_called()


def test_main_no_logpath(docker_client, session, mocker):
    args = Dict({
        "debug": False,
        "interval": 60
    })

    mocked_inspect = mocker.patch("logsql.__main__.Monitor.inspect")
    mocked_inspect.return_value = {
        "LogPath": ""
    }

    mocked_warning = mocker.patch("logging.warning")

    def _side_effect(message, *args, **kwargs):
        if message == "sleeping main thread":
            raise SystemExit()

    mocked_debug = mocker.patch("logging.debug")
    mocked_debug.side_effect = _side_effect

    logger = Logger(docker_client)
    try:
        main(args)
    finally:
        logger.container.kill()

    mocked_inspect.assert_called_once()
    mocked_warning.assert_called_once()


def test_main_logsql2(docker_client, session, mocker):
    args = Dict({
        "debug": False,
        "interval": .1
    })

    logger = None

    def _side_effect(message, *_args, **_kwargs):
        if message == "sleeping main thread":
            nonlocal logger
            if not logger:
                logger = Logger(docker_client, name="logsql")
            else:
                raise SystemExit()

    mocked_debug = mocker.patch("logging.debug")
    mocked_debug.side_effect = _side_effect

    mocked_add_container = mocker.patch("logsql.__main__.Monitor.add_container")

    try:
        main(args)
    finally:
        if logger:
            logger.container.kill()

    mocked_add_container.assert_not_called()


def test_main_manually_add_container(docker_client, session, mocker):
    args = Dict({
        "debug": False,
        "interval": .1
    })

    logger = None

    def _side_effect(message, *_args, **_kwargs):
        if message == "sleeping main thread":
            nonlocal logger
            if not logger:
                logger = Logger(docker_client)
            else:
                raise SystemExit()

    mocked_debug = mocker.patch("logging.debug")
    mocked_debug.side_effect = _side_effect

    mocked_add_container = mocker.patch("logsql.__main__.Monitor.add_container")

    try:
        main(args)
    finally:
        if logger:
            logger.container.kill()

    mocked_add_container.assert_called_with(logger.container.id)


def test_main_poll_container(logger, session, mocker):
    args = Dict({
        "debug": False,
        "interval": .1
    })

    done = False

    def _side_effect(*_args, **_kwargs):
        nonlocal done
        if not done:
            done = True
            return None
        raise SystemExit()

    mocked_poll = mocker.patch("subprocess.Popen.poll")
    mocked_poll.side_effect = _side_effect

    main(args)


def test_init(mocker):
    mocker.patch.object(__main__, "main", return_value=42)
    mocker.patch.object(__main__, "__name__", "__main__")
    mocked_exit = mocker.patch.object(__main__.sys, "exit")
    __main__.init()
    assert mocked_exit.call_args[0][0] == 42
