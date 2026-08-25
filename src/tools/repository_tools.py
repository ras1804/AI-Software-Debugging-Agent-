import ast
import re
from pathlib import Path

from pydantic import BaseModel, Field


class ListFilesInput(BaseModel):
    path: str = "."
    max_files: int = Field(default=200, ge=1, le=1000)


class ReadFileInput(BaseModel):
    path: str
    start_line: int = Field(default=1, ge=1)
    end_line: int = Field(default=250, ge=1)


class SearchCodeInput(BaseModel):
    query: str = Field(min_length=1)
    path: str = "."
    max_results: int = Field(default=50, ge=1, le=200)


class FindReferencesInput(BaseModel):
    symbol: str = Field(min_length=1)
    path: str = "."
    max_results: int = Field(default=100, ge=1, le=300)


class ToolContext:
    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()

    def safe_path(self, relative: str) -> Path:
        candidate = (self.workspace / relative).resolve()
        if candidate != self.workspace and self.workspace not in candidate.parents:
            raise ValueError("Path escapes repository workspace")
        return candidate

    def list_files(self, args: ListFilesInput) -> list[str]:
        root = self.safe_path(args.path)
        if not root.exists():
            raise FileNotFoundError(args.path)
        files = [str(p.relative_to(self.workspace)) for p in root.rglob("*") if p.is_file()]
        return sorted(files)[: args.max_files]

    def read_file(self, args: ReadFileInput) -> str:
        path = self.safe_path(args.path)
        if not path.is_file():
            raise FileNotFoundError(args.path)
        if path.stat().st_size > 1_000_000:
            raise ValueError("File exceeds 1 MB safety limit")
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(f"{i}: {line}" for i, line in enumerate(lines[args.start_line-1:args.end_line], args.start_line))

    def search_code(self, args: SearchCodeInput) -> list[str]:
        root = self.safe_path(args.path)
        results: list[str] = []
        pattern = re.compile(re.escape(args.query), re.IGNORECASE)
        for file in root.rglob("*.py"):
            if any(part in {".git", ".venv", "__pycache__"} for part in file.parts):
                continue
            text = file.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    results.append(f"{file.relative_to(self.workspace)}:{lineno}: {line.strip()}")
                    if len(results) >= args.max_results:
                        return results
        return results

    def find_references(self, args: FindReferencesInput) -> list[str]:
        results: list[str] = []
        for file in self.safe_path(args.path).rglob("*.py"):
            if any(part in {".git", ".venv", "__pycache__"} for part in file.parts):
                continue
            try:
                tree = ast.parse(file.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.Name, ast.Attribute)) and getattr(node, "id", getattr(node, "attr", "")) == args.symbol:
                    results.append(f"{file.relative_to(self.workspace)}:{node.lineno}: {args.symbol}")
                    if len(results) >= args.max_results:
                        return results
        return results
