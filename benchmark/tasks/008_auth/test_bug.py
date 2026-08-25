from auth import can_access
def test_admin():
    assert can_access({"role":"admin","id":1}, {"id":2})
