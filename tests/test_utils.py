from logsql import utils


def test_inode_number_not_found():
    assert utils.inode_number(__file__ + ".XXX") == -1


def test_nginx_log():
    # pylint: disable=line-too-long
    line = """1.1.1.1 - - [17/Aug/2019:23:18:39 +0000] "GET /etc/passwd HTTP/1.0" 400 166 "-" "-"\r\n"""  # noqa
    result = utils.parse_nginx_combined(line)
    assert result
    assert result["remote_addr"] == "1.1.1.1"
    assert result["remote_user"] == "-"
    assert result["datetime"] == "17/Aug/2019:23:18:39 +0000"
    assert result["request_method"] == "GET"
    assert result["url"] == "/etc/passwd"
    assert result["http_version"] == "HTTP/1.0"
    assert result["status_code"] == 400
    assert result["bytes_sent"] == 166
    assert result["referrer"] == "-"
    assert result["user_agent"] == "-"


def test_nginx_log_no_match():
    line = "BAD LOG LINE"
    assert utils.parse_nginx_combined(line) is None
