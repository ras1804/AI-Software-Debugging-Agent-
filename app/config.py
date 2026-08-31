
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    max_iterations: int = int(os.getenv("MAX_ITERATIONS", "3"))
    docker_timeout: int = int(os.getenv("DOCKER_TIMEOUT", "30"))
    mlflow_uri: str = os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")
    mlflow_experiment: str = os.getenv("MLFLOW_EXPERIMENT", "ai-debugging-agent")

settings = Settings()
