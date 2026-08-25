import subprocess
from pathlib import Path

from pydantic import BaseModel


class GitContext:
    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()

    def run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=self.workspace, text=True, capture_output=True, timeout=10)

    def create_branch(self, name: str = "agent/debug") -> str:
        safe = "".join(c for c in name if c.isalnum() or c in "-_/")
        if not safe:
            raise ValueError("Invalid branch name")
        result = self.run(["checkout", "-B", safe])
        if result.returncode:
            raise RuntimeError(result.stderr.strip())
        return safe

    def diff(self) -> str:
        result = self.run(["diff", "--no-ext-diff", "--"])
        if result.returncode:
            raise RuntimeError(result.stderr.strip())
        return result.stdout
