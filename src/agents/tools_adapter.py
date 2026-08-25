from langchain_core.tools import tool

from src.tools.repository_tools import FindReferencesInput, ListFilesInput, ReadFileInput, SearchCodeInput, ToolContext
from src.tools.quality_tools import QualityContext


def build_tools(ctx: ToolContext):
    @tool(args_schema=ListFilesInput)
    def list_files(path: str = ".", max_files: int = 200) -> list[str]:
        """List files in the repository."""
        return ctx.list_files(ListFilesInput(path=path, max_files=max_files))

    @tool(args_schema=ReadFileInput)
    def read_file(path: str, start_line: int = 1, end_line: int = 250) -> str:
        """Read a bounded section of a repository file."""
        return ctx.read_file(ReadFileInput(path=path, start_line=start_line, end_line=end_line))

    @tool(args_schema=SearchCodeInput)
    def search_code(query: str, path: str = ".", max_results: int = 50) -> list[str]:
        """Search Python source code for a text pattern."""
        return ctx.search_code(SearchCodeInput(query=query, path=path, max_results=max_results))

    @tool
    def inspect_tests(max_files: int = 100) -> list[str]:
        """Discover test files in the repository."""
        return QualityContext(ctx.workspace).inspect_tests(max_files)

    @tool
    def run_linter(path: str = ".") -> dict:
        """Run Ruff against a bounded repository path."""
        return QualityContext(ctx.workspace).run_linter(path)

    @tool(args_schema=FindReferencesInput)
    def find_references(symbol: str, path: str = ".", max_results: int = 100) -> list[str]:
        """Find Python AST references to a symbol."""
        return ctx.find_references(FindReferencesInput(symbol=symbol, path=path, max_results=max_results))

    return [list_files, read_file, search_code, find_references, inspect_tests, run_linter]
