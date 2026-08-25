from src.tools.quality_tools import QualityContext


def test_inspect_tests(tmp_path):
    (tmp_path / "test_a.py").write_text("def test_a(): pass\n")
    assert QualityContext(tmp_path).inspect_tests() == ["test_a.py"]
