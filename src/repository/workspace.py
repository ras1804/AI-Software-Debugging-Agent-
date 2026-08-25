import shutil
from pathlib import Path

from src.config.settings import get_settings


class WorkspaceManager:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or get_settings().workspace_root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, task_id: str, repository_path: str) -> Path:
        source = Path(repository_path).resolve()
        if not source.exists() or not source.is_dir():
            raise FileNotFoundError(f"Repository directory not found: {source}")
        destination = (self.root / task_id).resolve()
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "*.pyc"))
        self._init_git(destination)
        return destination

    def _init_git(self, path: Path) -> None:
        import subprocess
        subprocess.run(["git", "init", "-q"], cwd=path, check=True)
        subprocess.run(["git", "config", "user.email", "agent@example.local"], cwd=path, check=True)
        subprocess.run(["git", "config", "user.name", "Debugging Agent"], cwd=path, check=True)
        subprocess.run(["git", "add", "-A"], cwd=path, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=path, check=True)
        subprocess.run(["git", "checkout", "-qb", "agent/debug"], cwd=path, check=True)
