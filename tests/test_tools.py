
from app.tools import list_files, read_file, search_code

def test_repository_tools(tmp_path):
    (tmp_path / "x.py").write_text("print('hello')", encoding="utf-8")
    assert "x.py" in list_files(str(tmp_path))
    assert "hello" in read_file(str(tmp_path), "x.py")
    assert search_code(str(tmp_path), "hello") == ["x.py"]
