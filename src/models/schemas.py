from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


Status = Literal["queued", "running", "awaiting_approval", "approved", "rejected", "failed", "completed"]


class DebugRequest(BaseModel):
    repository_path: str
    bug_description: str = Field(min_length=5)
    stack_trace: str | None = None
    error_logs: str | None = None


class ToolCallRecord(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    success: bool = True
    duration_ms: float = 0


class TestResult(BaseModel):
    command: str
    return_code: int | None
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0
    timed_out: bool = False
    passed: bool = False


class Evidence(BaseModel):
    source: str
    detail: str


class Hypothesis(BaseModel):
    statement: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)


class FinalReport(BaseModel):
    problem: str
    root_cause: str
    evidence: list[str]
    files_investigated: list[str]
    files_changed: list[str]
    patch_summary: str
    tests_executed: list[str]
    test_results: list[TestResult]
    iterations: int
    limitations: list[str]
    recommendation: str


class DebugState(BaseModel):
    task_id: str
    repository_path: str
    workspace_path: str
    bug_description: str
    stack_trace: str | None = None
    error_logs: str | None = None
    investigation_plan: list[str] = Field(default_factory=list)
    files_inspected: list[str] = Field(default_factory=list)
    search_results: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    current_hypothesis: str | None = None
    patch: str | None = None
    patch_applied: bool = False
    test_commands: list[str] = Field(default_factory=list)
    test_results: list[TestResult] = Field(default_factory=list)
    iteration_count: int = 0
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    status: Status = "queued"
    approval_status: Literal["pending", "approved", "rejected"] = "pending"
    final_report: FinalReport | None = None
    diff: str = ""
    error: str | None = None


class DebugResponse(BaseModel):
    task_id: str
    status: Status
    message: str


class StatusResponse(BaseModel):
    task_id: str
    status: Status
    iteration_count: int
    approval_status: str
    error: str | None = None
    updated_at: datetime | None = None
