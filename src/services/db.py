from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from src.config.settings import get_settings


class Base(DeclarativeBase):
    pass


class DebugTask(Base):
    __tablename__ = "debug_tasks"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    repository_path: Mapped[str] = mapped_column(Text)
    workspace_path: Mapped[str] = mapped_column(Text)
    bug_description: Mapped[str] = mapped_column(Text)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_logs: Mapped[str | None] = mapped_column(Text, nullable=True)
    state_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


class Database:
    def __init__(self) -> None:
        settings = get_settings()
        url = settings.database_url
        if url.startswith("sqlite:///"):
            Path(url.removeprefix("sqlite:///" )).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(self.engine, expire_on_commit=False)

    def create_task(self, task: DebugTask) -> None:
        with self.Session() as session:
            session.add(task)
            session.commit()

    def get_task(self, task_id: str) -> DebugTask | None:
        with self.Session() as session:
            return session.get(DebugTask, task_id)

    def update_state(self, task_id: str, state: dict[str, Any], status: str | None = None) -> None:
        with self.Session() as session:
            task = session.get(DebugTask, task_id)
            if task is None:
                raise KeyError(task_id)
            task.state_json = state
            if status:
                task.status = status
            task.updated_at = datetime.now(timezone.utc)
            session.commit()
