from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./debugger.db"
    mlflow_tracking_uri: str = "./mlruns"
    mlflow_experiment: str = "ai-software-debugger"
    llm_provider: str = "openai"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    llm_temperature: float = Field(default=0.0, ge=0, le=2)
    demo_mode: bool = False
    max_iterations: int = Field(default=4, ge=1, le=10)
    tool_timeout_seconds: int = Field(default=20, ge=1, le=300)
    sandbox_memory: str = "512m"
    sandbox_cpus: str = "1"
    sandbox_pids: int = 128
    sandbox_network: str = "none"
    workspace_root: Path = Path("./workspace")
    benchmark_root: Path = Path("./benchmark/tasks")
    prompt_version: str = "v1"
    agent_version: str = "0.1.0"
    benchmark_version: str = "v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
