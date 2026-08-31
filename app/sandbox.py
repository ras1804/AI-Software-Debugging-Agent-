
import shutil
import subprocess
import tempfile
from pathlib import Path

def run_in_docker(repo_path: str, command: str = "pytest -q", timeout: int = 30):
    source = Path(repo_path).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(source, work, dirs_exist_ok=True)
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--cpus", "1",
            "--memory", "512m",
            "--pids-limit", "128",
            "-v", f"{work}:/workspace",
            "-w", "/workspace",
            "python:3.12-slim",
            "sh", "-lc",
            "pip install --disable-pip-version-check -q pytest && " + command,
        ]
        try:
            result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout)
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "exit_code": -1,
                "stdout": exc.stdout or "",
                "stderr": (exc.stderr or "") + "\nSandbox timeout",
                "timed_out": True,
            }
