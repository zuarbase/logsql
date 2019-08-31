import os

from logsql.offsetfile import OffsetFile


def cleanup(path):
    """ Delete any generated files """
    for _ in (path, path + OffsetFile.DEFAULT_SUFFIX):
        if os.path.exists(_):
            os.remove(_)
