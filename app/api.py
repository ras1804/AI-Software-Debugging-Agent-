
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .agent import run_debug

app = FastAPI(title="AI Software Debugging Agent")

class DebugRequest(BaseModel):
    repo_path: str
    bug_description: str = Field(min_length=5)
    stack_trace: str = ""
    test_command: str = "pytest -q"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/debug")
def debug(request: DebugRequest):
    try:
        result = run_debug(request.repo_path, request.bug_description,
                           request.stack_trace, request.test_command)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
