
from typing import TypedDict

class DebugState(TypedDict, total=False):
    repo_path: str
    bug_description: str
    stack_trace: str
    files: list[str]
    relevant_files: list[str]
    root_cause: str
    patch: str
    test_command: str
    test_output: str
    tests_passed: bool
    iterations: int
    approved: bool
    status: str
    error: str
    token_usage: int
    estimated_cost: float
