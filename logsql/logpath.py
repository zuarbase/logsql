""" Individual log file handling """
import os
import typing
import logging

from . import utils
from .offsetfile import OffsetFile


logger = logging.getLogger(__name__)


class LogPath:
    """ Class representation of a particular log file. """

    def __init__(
            self,
            path: str,
            encoding: str = "utf-8",
            newline: bytes = b"\n",
    ):
        self.path = path
        self.encoding = encoding
        self.newline = newline

        self.offsetfile = OffsetFile.read(path)
        self.buffer = b""
        self.lines = []  # buffered lines
        self.count = 0  # number of read lines

        inode = utils.inode_number(self.path)

        self.filp = open(self.path, "rb", buffering=0)
        if self.offsetfile:
            if inode == self.offsetfile.inode:
                self.filp.seek(self.offsetfile.offset, os.SEEK_SET)
            else:
                # There is no way to see if the file still exists but
                # was renamed, i.e. we can't open by ino.
                logger.warning("Inode changed, possible data loss")
                self.offsetfile.reset(inode=inode)
        else:
            self.offsetfile = OffsetFile(path, offset=0, inode=inode)

    def _read_last_chunk(self):
        chunk = self.filp.read()
        if not chunk:
            return

        last_index = chunk.rfind(self.newline)
        if last_index != -1:
            if last_index + len(self.newline) < len(chunk):
                logger.warning(
                    "Partial last line (not logged): %s",
                    chunk[last_index + len(self.newline):].decode(
                        self.encoding
                    )
                )
            self.buffer += chunk[0: last_index]
        else:
            logger.warning(
                "Partial chunk (not logged): %s",
            )

        lines = self.buffer.split(self.newline)
        for line in lines:
            line = line.strip()
            if line:
                self.lines.append(line.decode(self.encoding))
        self.buffer = b""

    def _readline_from_buffer(self):
        index = self.buffer.find(self.newline)
        if index == -1:
            return None
        result = self.buffer[0:index]
        length = index + len(self.newline)
        self.offsetfile.offset += length
        self.buffer = self.buffer[length:]
        return result.decode(self.encoding).strip() or None

    def readline(self) -> typing.Optional[str]:
        """ Read one line of the log file if available """
        inode = utils.inode_number(self.path)
        if inode != self.offsetfile.inode:
            # file change/rotation, read all remaining data.
            self._read_last_chunk()
            self.offsetfile.reset(inode=inode)

            if inode != -1:
                self.offsetfile.save()

            self.filp.close()

            if inode != -1:
                self.filp = open(self.path, "rb")
            else:
                self.filp = None

        # Cached line, nothing else is changed
        if self.lines:
            return self.lines.pop(0)

        if self.filp is None:
            raise FileNotFoundError(self.path)

        self.buffer += self.filp.read()

        result = self._readline_from_buffer()
        if result:
            self.count += 1
        return result

    def commit(self) -> None:
        """ Write the offset to disk """
        self.offsetfile.save()

    def close(self) -> None:
        """ Release all resources """
        self.filp.close()
