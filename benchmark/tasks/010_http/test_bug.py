from http_status import status
def test_ok():
    assert status(True) == 200
