""" Utility function s """
import re
import os
import subprocess
import typing

NGINX_COMBINED_REGEX = re.compile(
    # pylint:disable=line-too-long
    r"""\s*(?P<remote_addr>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - (?P<remote_user>\S+) \[(?P<datetime>\d{2}/[a-z]{3}/\d{4}:\d{2}:\d{2}:\d{2} ([+-]\d{4}))] \"(?P<request_method>\w+) (?P<url>\S+) (?P<http_version>[^"]+)" (?P<status_code__int>\d{3}) (?P<bytes_sent__int>\d+) (["](?P<referrer>(-)|(.+))["]) (["](?P<user_agent>.+)["])\s*""",  # noqa
    re.IGNORECASE
)


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

    user = os.environ.get("USER", "root")
    if user != "root":
        subprocess.run(
            ["sudo", "chown", "-R", user, path], check=True
        )


def parse_nginx_combined(
        line: str
) -> typing.Optional[dict]:
    """ Parse an NGINX combined line into a dict """
    match = NGINX_COMBINED_REGEX.match(line)
    if not match:
        return None

    result = {}
    for key, value in match.groupdict().items():
        tokens = key.split("__", 1)
        if len(tokens) == 1:
            result[key] = value
        else:
            # e.g. status_code__int -> status_code = int(value)
            result[tokens[0]] = __builtins__[tokens[1]](value)

    return result
