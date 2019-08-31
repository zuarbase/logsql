import os

from logsql.offsetfile import OffsetFile
from logsql.logpath import LogPath

from . import utils

PATH = "/tmp/test.log"


def test_logpath_basic():
    utils.cleanup(PATH)
    with open(PATH, "w") as filp:
        print("Hello World   ", file=filp)
        print("", file=filp)

    logpath = LogPath(PATH)
    assert logpath.readline() == "Hello World"
    assert logpath.readline() is None
    logpath.commit()

    offsetfile = OffsetFile.read(PATH)
    assert offsetfile.offset == 16

    logpath.close()


def test_logpath_rotation():
    utils.cleanup(PATH)
    with open(PATH, "w") as filp:
        print("line1", file=filp)

    logpath = LogPath(PATH)
    assert logpath.readline() == "line1"
    logpath.commit()

    with open(PATH, "a") as filp:
        print("line2", file=filp)
        filp.write("partial line to be lost")

    os.remove(PATH)

    with open(PATH, "w") as filp:
        print("line3", file=filp)

    assert logpath.readline() == "line2"
    assert logpath.readline() == "line3"


def test_logpath_empty_rotation():
    utils.cleanup(PATH)
    with open(PATH, "w") as filp:
        print("line1", file=filp)

    logpath = LogPath(PATH)
    assert logpath.readline() == "line1"
    logpath.commit()

    os.remove(PATH)

    with open(PATH, "w") as filp:
        print("line2", file=filp)

    assert logpath.readline() == "line2"


def test_logpath_existing():
    utils.cleanup(PATH)
    with open(PATH, "w") as filp:
        print("Hello World!", file=filp)

    logpath = LogPath(PATH)
    while logpath.readline():
        pass
    logpath.commit()

    logpath = LogPath(PATH)
    assert logpath.offsetfile.offset == 13


def test_logpath_lost_rotation():
    utils.cleanup(PATH)
    with open(PATH, "w") as filp:
        print("Hello World", file=filp)

    logpath = LogPath(PATH)
    while logpath.readline():
        pass
    logpath.commit()

    os.remove(PATH)

    with open(PATH, "w") as filp:
        print("Hello Again", file=filp)

    logpath = LogPath(PATH)
    assert logpath.offsetfile.offset == 0


def test_logpath_last_chunk():
    utils.cleanup(PATH)
    with open(PATH, "w") as filp:
        filp.write("lost last chunk")

    logpath = LogPath(PATH)
    os.remove(PATH)

    with open(PATH, "w") as filp:
        filp.write("Hello Again\n")

    assert logpath.readline() == "Hello Again"

    logpath.commit()
    assert logpath.offsetfile.offset == 12
