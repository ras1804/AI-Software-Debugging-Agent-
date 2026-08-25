from contextlib import contextmanager

import mlflow

from src.config.settings import get_settings


@contextmanager
def task_run(task_id: str):
    settings = get_settings()
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment)
    with mlflow.start_run(run_name=task_id):
        mlflow.log_params({"agent_version": settings.agent_version, "prompt_version": settings.prompt_version, "model": settings.openai_model, "benchmark_version": settings.benchmark_version})
        yield
