import json
import time
from pathlib import Path

from src.agents.graph import DebuggingAgent
from src.config.settings import get_settings
from src.models.schemas import DebugState
from src.services.task_store import TaskStore
from src.repository.workspace import WorkspaceManager


def load_tasks(root: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(root.glob("*/task.json"))]


def evaluate() -> dict:
    settings = get_settings()
    tasks = load_tasks(settings.benchmark_root)
    agent = DebuggingAgent(TaskStore())
    results = []
    for task in tasks:
        task_id = f"eval-{task['id']}-{int(time.time())}"
        workspace = WorkspaceManager(settings.workspace_root).create(task_id, str(Path(task["repository"])))
        state = DebugState(task_id=task_id, repository_path=task["repository"], workspace_path=str(workspace), bug_description=task["bug_description"], stack_trace=task.get("stack_trace"))
        started = time.perf_counter()
        final = agent.run(state)
        latency = time.perf_counter() - started
        passed = bool(final.test_results) and all(r.passed for r in final.test_results[-len(final.test_commands or ["x"]):])
        expected = task.get("known_root_cause", "").lower()
        actual = (final.current_hypothesis or "").lower()
        root_accuracy = bool(expected and any(token in actual for token in expected.split() if len(token) > 4))
        results.append({"task_id": task["id"], "success": passed, "root_cause_accuracy": root_accuracy, "iterations": final.iteration_count, "tool_calls": len(final.tool_calls), "latency_seconds": latency, "status": final.status})
    total = len(results) or 1
    summary = {"benchmark_version": settings.benchmark_version, "tasks": results, "metrics": {"task_success_rate": sum(r["success"] for r in results)/total, "root_cause_accuracy": sum(r["root_cause_accuracy"] for r in results)/total, "average_iterations": sum(r["iterations"] for r in results)/total, "average_tool_calls": sum(r["tool_calls"] for r in results)/total, "average_latency": sum(r["latency_seconds"] for r in results)/total}}
    Path("evaluation_report.json").write_text(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
