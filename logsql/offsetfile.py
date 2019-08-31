"""
Offset files store the current inode number and the last read offset
for a given log file.  The inode is stored in case the file is rotated
between reads.
"""
import os

DEFAULT_SUFFIX = ".offsetfile"


class OffsetFile:
    """ The stored file position """
    DEFAULT_SUFFIX = DEFAULT_SUFFIX

    def __init__(
            self,
            path: str,
            *,
            suffix: str = DEFAULT_SUFFIX,
            offset: int = None,
            inode: int = None
    ):
        if not path.endswith(suffix):
            path = path + suffix
        self.path = path

        if offset is not None:
            assert inode >= 0
        if inode is not None:
            assert offset >= 0

        self.offset = offset
        self.inode = inode

    def save(self) -> None:
        """ Write the current state to disk. """
        assert self.path
        assert self.inode >= 0
        assert self.offset >= 0
        with open(self.path, "w") as filp:
            print(str(self.inode), file=filp)
            print(str(self.offset), file=filp)

    def reset(
            self,
            inode: int,
            offset: int = 0
    ):
        """ Reset to a new file """
        self.inode = inode
        self.offset = offset

    @classmethod
    def read(
            cls,
            path: str,
            suffix=DEFAULT_SUFFIX
    ):
        """ Retrieve the offset/inode from the file system """
        if not path.endswith(suffix):
            path = path + suffix

        if not os.path.exists(path):
            return None

        with open(path, "r") as filp:
            contents = filp.read().strip()
        lines = contents.splitlines()
        if len(lines) != 2:
            raise IOError(
                "Invalid offsetfile format: incorrect number of lines"
            )

        offsetfile = OffsetFile(path)
        try:
            offsetfile.inode = int(lines[0])
            offsetfile.offset = int(lines[1])
        except ValueError as ex:
            raise IOError("Invalid offsetfile format: " + str(ex))

        return offsetfile
