import shutil
import subprocess
import time
from pathlib import Path

from src.config.settings import get_settings
from src.models.schemas import TestResult


class DockerUnavailable(RuntimeError):
    pass


class DockerSandbox:
    def __init__(self) -> None:
        self.settings = get_settings()

    def available(self) -> bool:
        return shutil.which("docker") is not None

    def run(self, workspace: Path, command: str, timeout: int | None = None) -> TestResult:
        if not self.available():
            raise DockerUnavailable("Docker CLI is not installed or unavailable")
        if not command.startswith(("pytest", "python -m pytest", "ruff check")):
            raise ValueError("Sandbox command is not allowlisted")
        timeout = timeout or self.settings.tool_timeout_seconds
        start = time.perf_counter()
        image = "ai-software-debugger-sandbox:latest"
        argv = [
            "docker", "run", "--rm",
            "--network", self.settings.sandbox_network,
            "--cpus", self.settings.sandbox_cpus,
            "--memory", self.settings.sandbox_memory,
            "--pids-limit", str(self.settings.sandbox_pids),
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges:true",
            "-v", f"{workspace.resolve()}:/workspace:rw",
            "-w", "/workspace",
            image,
            "sh", "-lc", command,
        ]
        try:
            result = subprocess.run(argv, text=True, capture_output=True, timeout=timeout + 10)
            return TestResult(command=command, return_code=result.returncode, stdout=result.stdout[-12000:], stderr=result.stderr[-12000:], duration_ms=(time.perf_counter()-start)*1000, passed=result.returncode == 0)
        except subprocess.TimeoutExpired as exc:
            return TestResult(command=command, return_code=None, stdout=str(exc.stdout or "")[-12000:], stderr=str(exc.stderr or "")[-12000:], duration_ms=(time.perf_counter()-start)*1000, timed_out=True, passed=False)
