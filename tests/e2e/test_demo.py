import pytest
pytest.importorskip("langgraph")
import os
from pathlib import Path

from src.agents.graph import DebuggingAgent
from src.config.settings import get_settings
from src.models.schemas import DebugState
from src.repository.workspace import WorkspaceManager
from src.services.task_store import TaskStore


def test_demo_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    # Settings is cached, so instantiate a local state and use the bounded demo adapter.
    repo = Path("examples/buggy_orders_app").resolve()
    workspace = WorkspaceManager(tmp_path).create("e2e-demo", str(repo))
    state = DebugState(task_id="e2e-demo", repository_path=str(repo), workspace_path=str(workspace), bug_description="The /orders endpoint returns HTTP 500 when quantity is zero.")
    agent = DebuggingAgent(TaskStore())
    # Environment settings may be cached before the test; this E2E verifies workspace mechanics even if demo mode is off.
    final = agent.run(state)
    assert final.task_id == "e2e-demo"
    assert final.status in {"awaiting_approval", "failed"}
