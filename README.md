# AI Software Debugging Agent

A compact agentic debugging system using LangGraph, an LLM with tool calling, FastAPI, Streamlit, Docker, MLflow, pytest, and GitHub Actions.

## Architecture

User -> FastAPI/Streamlit -> LangGraph -> inspect -> patch -> Docker sandbox -> tests -> approval / re-plan.

The agent never applies a patch to the user's original repository during validation. It copies the repository to a temporary directory, applies the candidate patch there, and executes tests in Docker.

## Setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Put your LLM API key in `.env`. Install and start Docker Desktop.

## Run API

```powershell
uvicorn app.api:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## Run Streamlit

```powershell
streamlit run streamlit_app.py
```

## Tests

```powershell
pytest -q
```

## MLflow

```powershell
mlflow ui --backend-store-uri ./mlruns
```

Then run:

```powershell
python benchmark/evaluate.py
```

## Docker

```powershell
docker build -t ai-debugging-agent .
docker run --rm -p 8000:8000 --env-file .env ai-debugging-agent
```

## Important sandbox limitation

The sandbox uses Docker with no network, CPU/memory/PID limits, a temporary mounted copy, and a timeout. This is a practical learning-project isolation layer, not a guaranteed security boundary for hostile code. A production service executing arbitrary untrusted repositories needs stronger isolation, hardened images, syscall restrictions, non-root execution, resource quotas, image scanning, and additional containment.

## Human approval

A successful test run changes the workflow to `awaiting_human_approval`. The displayed patch must be reviewed by a human before it is accepted into the real repository. This project intentionally does not silently modify the original repository.

## Benchmark

Five small buggy repositories live under `benchmark/tasks`. `benchmark/evaluate.py` runs each task and records basic metrics in MLflow. Root-cause and patch semantic scoring are intentionally kept simple in this first version.

## CI/CD

GitHub Actions installs dependencies, runs pytest, and builds the Docker image.

## Resume mapping

- Agentic debugging: `app/agent.py`
- Repository inspection: `app/tools.py`
- Patch validation/application: `app/patcher.py`
- Docker sandbox: `app/sandbox.py`
- API: `app/api.py`
- UI: `streamlit_app.py`
- MLflow benchmark: `benchmark/evaluate.py`
- Testing: `tests/`
- CI/CD: `.github/workflows/ci.yml`

## Limitations / next steps

The current implementation uses bounded source context and an explicit patch format rather than a full code-indexing system. LLM token/cost fields are only populated when the provider exposes them and are not fabricated. For a production system, add structured tool calling, stronger patch parsing, approval persistence, richer benchmark scoring, model-provider abstraction, authentication, audit logs, and stronger sandboxing.
