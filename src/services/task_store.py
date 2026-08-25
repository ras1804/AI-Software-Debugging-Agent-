import json
from typing import Any

from src.models.schemas import DebugState
from src.services.db import Database


class TaskStore:
    def __init__(self, db: Database | None = None) -> None:
        self.db = db or Database()

    def save(self, state: DebugState) -> None:
        payload = json.loads(state.model_dump_json())
        self.db.update_state(state.task_id, payload, state.status)

    def load(self, task_id: str) -> DebugState:
        task = self.db.get_task(task_id)
        if not task:
            raise KeyError(task_id)
        return DebugState.model_validate(task.state_json)

    def raw(self, task_id: str) -> dict[str, Any]:
        task = self.db.get_task(task_id)
        if not task:
            raise KeyError(task_id)
        return task.state_json
