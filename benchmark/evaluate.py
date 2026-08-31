
import json
import time
from pathlib import Path
import mlflow
from app.agent import run_debug
from app.config import settings

ROOT = Path(__file__).resolve().parent
tasks = json.loads((ROOT / "tasks.json").read_text())

mlflow.set_tracking_uri(settings.mlflow_uri)
mlflow.set_experiment(settings.mlflow_experiment)

for task in tasks:
    repo = str(ROOT / task["repo"])
    start = time.perf_counter()
    with mlflow.start_run(run_name=task["task_id"]):
        result = run_debug(repo, task["bug_description"])
        latency = time.perf_counter() - start
        mlflow.log_params({"model": settings.model, "task_id": task["task_id"]})
        mlflow.log_metrics({
            "task_success": int(result.get("tests_passed", False)),
            "tests_passed": int(result.get("tests_passed", False)),
            "iterations": result.get("iterations", 0),
            "latency": latency,
        })
        print(task["task_id"], result.get("status"), f"{latency:.2f}s")
