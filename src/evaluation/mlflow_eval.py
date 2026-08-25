import json
from pathlib import Path

import mlflow

from src.config.settings import get_settings
from src.evaluation.runner import evaluate


def run() -> dict:
    settings = get_settings()
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment)
    with mlflow.start_run(run_name=f"agent-{settings.agent_version}"):
        summary = evaluate()
        mlflow.log_params({"model": settings.openai_model, "temperature": settings.llm_temperature, "prompt_version": settings.prompt_version, "agent_version": settings.agent_version, "benchmark_version": settings.benchmark_version, "max_iterations": settings.max_iterations})
        mlflow.log_metrics(summary["metrics"])
        mlflow.log_artifact("evaluation_report.json")
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
