import subprocess
from pathlib import Path


class PatchManager:
    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()

    def validate_and_apply(self, patch: str) -> None:
        if not patch.strip() or len(patch) > 200_000:
            raise ValueError("Patch is empty or too large")
        check = subprocess.run(["git", "apply", "--check", "--whitespace=error-all", "-"], cwd=self.workspace, input=patch, text=True, capture_output=True, timeout=10)
        if check.returncode:
            raise ValueError(f"Patch validation failed: {check.stderr.strip()}")
        apply = subprocess.run(["git", "apply", "--whitespace=error-all", "-"], cwd=self.workspace, input=patch, text=True, capture_output=True, timeout=10)
        if apply.returncode:
            raise RuntimeError(f"Patch application failed: {apply.stderr.strip()}")
