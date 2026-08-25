import json
import logging
import sys
from contextvars import ContextVar

_task_id: ContextVar[str] = ContextVar("task_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "task_id": _task_id.get(),
            "message": record.getMessage(),
        }
        return json.dumps(payload, ensure_ascii=False)


def set_task_id(task_id: str) -> None:
    _task_id.set(task_id)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level)
