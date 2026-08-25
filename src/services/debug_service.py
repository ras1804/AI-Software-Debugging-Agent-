import threading
import uuid
from pathlib import Path

from src.agents.graph import DebuggingAgent
from src.models.schemas import DebugRequest, DebugState
from src.observability.logging import set_task_id
from src.repository.workspace import WorkspaceManager
from src.services.db import Database, DebugTask
from src.services.task_store import TaskStore


class DebugService:
    def __init__(self) -> None:
        self.db = Database()
        self.store = TaskStore(self.db)
        self.workspace = WorkspaceManager()
        self.agent = DebuggingAgent(self.store)

    def create(self, request: DebugRequest) -> DebugState:
        task_id = uuid.uuid4().hex
        workspace = self.workspace.create(task_id, request.repository_path)
        state = DebugState(task_id=task_id, repository_path=str(Path(request.repository_path).resolve()), workspace_path=str(workspace), bug_description=request.bug_description, stack_trace=request.stack_trace, error_logs=request.error_logs)
        self.db.create_task(DebugTask(id=task_id, status="queued", repository_path=state.repository_path, workspace_path=str(workspace), bug_description=request.bug_description, stack_trace=request.stack_trace, error_logs=request.error_logs, state_json=state.model_dump(mode="json")))
        return state

    def start(self, task_id: str) -> None:
        def worker() -> None:
            set_task_id(task_id)
            state = self.store.load(task_id)
            self.agent.run(state)
        threading.Thread(target=worker, daemon=True, name=f"debug-{task_id[:8]}").start()

    def approve(self, task_id: str) -> DebugState:
        state = self.store.load(task_id)
        if state.status != "awaiting_approval":
            raise ValueError("Task is not awaiting approval")
        state.approval_status = "approved"
        state.status = "completed"
        self.store.save(state)
        return state

    def reject(self, task_id: str) -> DebugState:
        state = self.store.load(task_id)
        if state.status != "awaiting_approval":
            raise ValueError("Task is not awaiting approval")
        state.approval_status = "rejected"
        state.status = "rejected"
        self.store.save(state)
        return state
