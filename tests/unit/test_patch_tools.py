from pathlib import Path

import pytest

from src.tools.patch_tools import PatchManager


def test_patch_apply(tmp_path: Path):
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "a@b"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "a"], cwd=tmp_path, check=True)
    (tmp_path / "x.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    patch = """diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"""
    PatchManager(tmp_path).validate_and_apply(patch)
    assert (tmp_path / "x.py").read_text() == "x = 2\n"


def test_bad_patch_rejected(tmp_path: Path):
    (tmp_path / "x.py").write_text("x = 1\n")
    with pytest.raises(Exception):
        PatchManager(tmp_path).validate_and_apply("not a patch")
