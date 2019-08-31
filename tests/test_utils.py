from logsql import utils


def test_inode_number_not_found():
    assert utils.inode_number(__file__ + ".XXX") == -1
