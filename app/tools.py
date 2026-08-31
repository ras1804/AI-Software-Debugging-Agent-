
from pathlib import Path
import subprocess

IGNORED = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules"}

def list_files(repo_path: str) -> list[str]:
    root = Path(repo_path)
    return [str(p.relative_to(root)) for p in root.rglob("*")
            if p.is_file() and not any(part in IGNORED for part in p.parts)]

def read_file(repo_path: str, path: str) -> str:
    root = Path(repo_path).resolve()
    target = (root / path).resolve()
    if root not in target.parents and target != root:
        raise ValueError("Path escapes repository")
    return target.read_text(encoding="utf-8")

def search_code(repo_path: str, query: str) -> list[str]:
    matches = []
    for rel in list_files(repo_path):
        if not rel.endswith(".py"):
            continue
        try:
            text = read_file(repo_path, rel)
        except (UnicodeDecodeError, OSError):
            continue
        if query.lower() in text.lower():
            matches.append(rel)
    return matches

def run_tests_local(repo_path: str, command: str = "pytest -q", timeout: int = 30):
    result = subprocess.run(command, cwd=repo_path, shell=True, capture_output=True,
                            text=True, timeout=timeout)
    return result.returncode, result.stdout, result.stderr
