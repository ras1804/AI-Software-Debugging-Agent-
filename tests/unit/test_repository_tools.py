from pathlib import Path

import pytest

from src.tools.repository_tools import ListFilesInput, ReadFileInput, SearchCodeInput, ToolContext


def test_workspace_escape_is_blocked(tmp_path: Path):
    ctx = ToolContext(tmp_path)
    with pytest.raises(ValueError):
        ctx.read_file(ReadFileInput(path="../secret.txt"))


def test_search_and_read(tmp_path: Path):
    (tmp_path / "a.py").write_text("def hello():\n    return 42\n")
    ctx = ToolContext(tmp_path)
    assert "a.py" in ctx.list_files(ListFilesInput())[0]
    assert "return 42" in ctx.read_file(ReadFileInput(path="a.py"))
    assert ctx.search_code(SearchCodeInput(query="hello"))
