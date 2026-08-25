import subprocess
from pathlib import Path


class QualityContext:
    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()

    def inspect_tests(self, max_files: int = 100) -> list[str]:
        files = sorted({*self.workspace.rglob("test_*.py"), *self.workspace.rglob("*_test.py")})
        return [str(p.relative_to(self.workspace)) for p in files[:max_files]]

    def run_linter(self, path: str = ".") -> dict:
        target = (self.workspace / path).resolve()
        if target != self.workspace and self.workspace not in target.parents:
            raise ValueError("Path escapes repository workspace")
        result = subprocess.run(["ruff", "check", str(target)], cwd=self.workspace, text=True, capture_output=True, timeout=20)
        return {"return_code": result.returncode, "stdout": result.stdout[-8000:], "stderr": result.stderr[-8000:], "passed": result.returncode == 0}
