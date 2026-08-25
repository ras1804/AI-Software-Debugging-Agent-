import re
import subprocess
import time
from pathlib import Path

from src.models.schemas import TestResult


ALLOWED_COMMANDS = {
    "pytest": ["pytest"],
    "python -m pytest": ["python", "-m", "pytest"],
    "ruff check": ["ruff", "check"],
}


class CommandRunner:
    def __init__(self, workspace: Path, timeout: int = 20):
        self.workspace = workspace.resolve()
        self.timeout = timeout

    def parse_command(self, command: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", command.strip())
        for prefix, argv in ALLOWED_COMMANDS.items():
            if normalized == prefix or normalized.startswith(prefix + " "):
                suffix = normalized[len(prefix):].strip()
                if any(x in suffix for x in [";", "&&", "||", "|", ">", "<", "`", "$", "../"]):
                    raise ValueError("Unsafe test command")
                return argv + suffix.split()
        raise ValueError(f"Command not allowlisted: {command}")

    def run(self, command: str) -> TestResult:
        argv = self.parse_command(command)
        start = time.perf_counter()
        try:
            result = subprocess.run(argv, cwd=self.workspace, text=True, capture_output=True, timeout=self.timeout)
            return TestResult(command=command, return_code=result.returncode, stdout=result.stdout[-12000:], stderr=result.stderr[-12000:], duration_ms=(time.perf_counter()-start)*1000, passed=result.returncode == 0)
        except subprocess.TimeoutExpired as exc:
            return TestResult(command=command, return_code=None, stdout=str(exc.stdout or "")[-12000:], stderr=str(exc.stderr or "")[-12000:], duration_ms=(time.perf_counter()-start)*1000, timed_out=True, passed=False)
