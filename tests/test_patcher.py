
from app.patcher import apply_patch

def test_apply_patch(tmp_path):
    p = tmp_path / "x.py"
    p.write_text("return 1\n", encoding="utf-8")
    patch = """FILE: x.py
OLD:
return 1
END_OLD
NEW:
return 2
END_NEW"""
    assert apply_patch(str(tmp_path), patch) == ["x.py"]
    assert p.read_text() == "return 2\n"
