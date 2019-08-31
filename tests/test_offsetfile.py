import os

import pytest

from logsql.offsetfile import OffsetFile
from . import utils

PATH = "/tmp/test.log"


def test_offsetfile():
    utils.cleanup(PATH)
    with open(PATH, "w") as filp:
        print("hello world", file=filp)

    info = os.stat(PATH)
    inode = info.st_ino

    offsetfile = OffsetFile.read(PATH)
    assert offsetfile is None

    offsetfile = OffsetFile(PATH)
    offsetfile.inode = inode
    offsetfile.offset = 17

    offsetfile.save()

    offsetfile = OffsetFile.read(PATH)
    assert offsetfile.path == PATH + OffsetFile.DEFAULT_SUFFIX
    assert offsetfile.inode == inode
    assert offsetfile.offset == 17


def test_offsetfile_bad_lines():
    path = PATH + OffsetFile.DEFAULT_SUFFIX
    with open(path, "w") as filp:
        filp.write("line1\nline2\nline3\n")
    with pytest.raises(IOError) as ex:
        OffsetFile.read(PATH)
    assert "incorrect number of lines" in str(ex.value)


def test_offsetfile_bad_values():
    path = PATH + OffsetFile.DEFAULT_SUFFIX
    with open(path, "w") as filp:
        filp.write("line1\n34\n")
    with pytest.raises(IOError) as ex:
        OffsetFile.read(PATH)
    assert "invalid literal" in str(ex.value)
