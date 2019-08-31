""" Utility function s """
import os
import subprocess


def inode_number(
        path: str
):
    """ Get the inode number for the given path, returns -1 on error """
    try:
        st_buf = os.stat(path)
        return st_buf.st_ino
    except FileNotFoundError:
        return -1


def containers_chown(
        path: str
):
    """ Change the owner of the containers path """
    index = path.index("/containers")
    assert index > 0

    path = path[0: index + len("/containers")]
    if os.environ["USER"] != "root":
        subprocess.run(
            ["sudo", "chown", "-R", os.environ["USER"], path], check=True
        )
