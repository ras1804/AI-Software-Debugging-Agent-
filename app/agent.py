
import json
import re
import shutil
import tempfile
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .config import settings
from .state import DebugState
from .tools import list_files, read_file
from .patcher import apply_patch
from .sandbox import run_in_docker

SYSTEM = """You are a Python debugging agent. Inspect the supplied repository context.
Return concise, evidence-based answers. When generating a patch, use exactly:
FILE: relative/path.py
OLD:
exact old text
END_OLD
NEW:
replacement text
END_NEW
Do not invent files or code that was not inspected."""

def _model():
    if not settings.api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return ChatOpenAI(model=settings.model, temperature=0, api_key=settings.api_key)

def analyze_bug(state: DebugState):
    state["status"] = "analyzing"
    model = _model()
    prompt = f"Bug: {state['bug_description']}\nStack trace: {state.get('stack_trace','')}\n"
    response = model.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)])
    state["root_cause"] = response.content
    return state

def inspect_repo(state: DebugState):
    files = list_files(state["repo_path"])
    state["files"] = files
    # Give the model a bounded amount of source context.
    chunks = []
    for rel in files:
        if rel.endswith(".py"):
            try:
                text = read_file(state["repo_path"], rel)
                chunks.append(f"\n--- {rel} ---\n{text[:8000]}")
            except Exception:
                pass
        if len("".join(chunks)) > 30000:
            break
    model = _model()
    prompt = (f"Bug: {state['bug_description']}\n"
              f"Current hypothesis: {state.get('root_cause','')}\n"
              f"Repository:\n{''.join(chunks)}\n"
              "Identify the most relevant files and explain the evidence. "
              "Return JSON: {\"relevant_files\": [...], \"root_cause\": \"...\"}")
    response = model.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)])
    try:
        data = json.loads(response.content)
    except json.JSONDecodeError:
        data = {"relevant_files": [x for x in files if x.endswith(".py")][:5],
                "root_cause": response.content}
    state["relevant_files"] = data.get("relevant_files", [])
    state["root_cause"] = data.get("root_cause", state.get("root_cause", ""))
    return state

def generate_patch(state: DebugState):
    context = []
    for rel in state.get("relevant_files", [])[:5]:
        try:
            context.append(f"--- {rel} ---\n{read_file(state['repo_path'], rel)[:12000]}")
        except Exception:
            pass
    model = _model()
    prompt = (f"Bug: {state['bug_description']}\n"
              f"Root cause: {state['root_cause']}\n"
              f"Previous test output: {state.get('test_output','')[-8000:]}\n"
              f"Code:\n{''.join(context)}\n"
              "Generate the smallest correct patch. Return ONLY patch blocks.")
    response = model.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)])
    state["patch"] = response.content
    return state

def run_tests(state: DebugState):
    state["status"] = "testing"
    # Work on an isolated copy; never mutate the original repository.
    isolated = tempfile.mkdtemp(prefix="debug-agent-")
    shutil.copytree(state["repo_path"], isolated, dirs_exist_ok=True)
    try:
        apply_patch(isolated, state["patch"])
        result = run_in_docker(isolated, state.get("test_command", "pytest -q"), settings.docker_timeout)
        state["tests_passed"] = result["exit_code"] == 0 and not result["timed_out"]
        state["test_output"] = result["stdout"] + "\n" + result["stderr"]
        state["status"] = "tests_passed" if state["tests_passed"] else "tests_failed"
    finally:
        shutil.rmtree(isolated, ignore_errors=True)
    state["iterations"] = state.get("iterations", 0) + 1
    return state

def route_after_tests(state: DebugState):
    if state.get("tests_passed"):
        return "approval"
    if state.get("iterations", 0) >= settings.max_iterations:
        return "finish"
    return "replan"

def approval(state: DebugState):
    # API/UI supplies approval separately. This node represents the gate.
    state["status"] = "awaiting_human_approval"
    return state

def replan(state: DebugState):
    state["status"] = "replanning"
    return state

def build_graph():
    graph = StateGraph(DebugState)
    graph.add_node("analyze", analyze_bug)
    graph.add_node("inspect", inspect_repo)
    graph.add_node("patch", generate_patch)
    graph.add_node("test", run_tests)
    graph.add_node("replan", replan)
    graph.add_node("approval", approval)
    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "inspect")
    graph.add_edge("inspect", "patch")
    graph.add_edge("patch", "test")
    graph.add_conditional_edges("test", route_after_tests,
                                {"approval": "approval", "replan": "replan", "finish": END})
    graph.add_edge("replan", "patch")
    graph.add_edge("approval", END)
    return graph.compile()

def run_debug(repo_path, bug_description, stack_trace="", test_command="pytest -q"):
    initial: DebugState = {
        "repo_path": repo_path, "bug_description": bug_description,
        "stack_trace": stack_trace, "test_command": test_command,
        "iterations": 0, "approved": False
    }
    return build_graph().invoke(initial)
