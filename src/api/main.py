from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import get_settings
from src.models.schemas import DebugRequest, DebugResponse, StatusResponse
from src.observability.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
service = None

def get_service():
    global service
    if service is None:
        from src.services.debug_service import DebugService
        service = DebugService()
    return service


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="AI Software Debugger", version=settings.agent_version, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/debug", response_model=DebugResponse)
def debug(request: DebugRequest):
    try:
        state = get_service().create(request)
        get_service().start(state.task_id)
        return DebugResponse(task_id=state.task_id, status="queued", message="Debugging task started")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/debug/{task_id}", response_model=StatusResponse)
def get_debug(task_id: str):
    try:
        state = get_service().store.load(task_id)
        return StatusResponse(task_id=state.task_id, status=state.status, iteration_count=state.iteration_count, approval_status=state.approval_status, error=state.error)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


@app.get("/debug/{task_id}/status", response_model=StatusResponse)
def status(task_id: str):
    return get_debug(task_id)


@app.get("/debug/{task_id}/report")
def report(task_id: str):
    try:
        state = get_service().store.load(task_id)
        return state.final_report.model_dump() if state.final_report else {"status": state.status}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


@app.get("/debug/{task_id}/diff")
def diff(task_id: str):
    try:
        state = get_service().store.load(task_id)
        return {"diff": state.diff}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


@app.post("/debug/{task_id}/approve")
def approve(task_id: str):
    try:
        return get_service().approve(task_id).model_dump()
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/debug/{task_id}/reject")
def reject(task_id: str):
    try:
        return get_service().reject(task_id).model_dump()
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
