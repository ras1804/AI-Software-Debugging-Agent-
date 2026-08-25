from pathlib import Path

import pytest

from src.tools.test_tools import CommandRunner


def test_command_allowlist(tmp_path: Path):
    runner = CommandRunner(tmp_path)
    assert runner.parse_command("python -m pytest -q")[0:3] == ["python", "-m", "pytest"]
    with pytest.raises(ValueError):
        runner.parse_command("rm -rf /")
    with pytest.raises(ValueError):
        runner.parse_command("pytest; whoami")
