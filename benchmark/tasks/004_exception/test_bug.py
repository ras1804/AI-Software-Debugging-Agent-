from parser import parse_int
def test_bad_value():
    assert parse_int("abc") is None
