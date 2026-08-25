import json
import logging
import time
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.llm import LLMClient
from src.agents.schemas import CriticOutput, HypothesisOutput, PatchOutput, PlanOutput
from src.agents.tools_adapter import build_tools
from src.config.settings import get_settings
from src.models.schemas import DebugState, Evidence, FinalReport, Hypothesis, TestResult, ToolCallRecord
from src.repository.workspace import WorkspaceManager
from src.sandbox.docker_runner import DockerSandbox, DockerUnavailable
from src.services.task_store import TaskStore
from src.tools.git_tools import GitContext
from src.tools.patch_tools import PatchManager
from src.tools.repository_tools import ToolContext
from src.tools.test_tools import CommandRunner

logger = logging.getLogger(__name__)

SYSTEM = Path("prompts/debugger_system.md").read_text(encoding="utf-8") if Path("prompts/debugger_system.md").exists() else "You are a senior software debugging agent."


class GraphState(TypedDict):
    state: dict[str, Any]


def _model(state: GraphState) -> DebugState:
    return DebugState.model_validate(state["state"])


def _pack(s: DebugState) -> dict[str, Any]:
    return {"state": json.loads(s.model_dump_json())}


class DebuggingAgent:
    def __init__(self, store: TaskStore | None = None):
        self.settings = get_settings()
        self.store = store or TaskStore()
        self.llm = LLMClient()
        self.sandbox = DockerSandbox()
        self.graph = self._build_graph()

    def _build_graph(self):
        g = StateGraph(GraphState)
        g.add_node("plan", self.plan)
        g.add_node("investigate", self.investigate)
        g.add_node("hypothesis", self.hypothesis)
        g.add_node("patch", self.patch)
        g.add_node("execute", self.execute)
        g.add_node("critic", self.critic)
        g.add_node("report", self.report)
        g.add_edge(START, "plan")
        g.add_edge("plan", "investigate")
        g.add_edge("investigate", "hypothesis")
        g.add_edge("hypothesis", "patch")
        g.add_edge("patch", "execute")
        g.add_conditional_edges("execute", self.after_execute, {"retry": "hypothesis", "critic": "critic", "failed": "report"})
        g.add_conditional_edges("critic", self.after_critic, {"retry": "hypothesis", "report": "report"})
        g.add_edge("report", END)
        return g.compile()

    def run(self, state: DebugState) -> DebugState:
        state.status = "running"
        self.store.save(state)
        try:
            result = self.graph.invoke(_pack(state))
            final = DebugState.model_validate(result["state"])
            self.store.save(final)
            return final
        except Exception as exc:
            state.status = "failed"
            state.error = str(exc)
            self.store.save(state)
            logger.exception("agent_failed")
            return state

    def plan(self, gs: GraphState) -> dict[str, Any]:
        s = _model(gs)
        if self.llm.enabled:
            structured = self.llm.llm.with_structured_output(PlanOutput)
            out = structured.invoke([{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"Create a concise investigation plan for:\n{s.bug_description}\nStack trace:\n{s.stack_trace or 'none'}"}])
            s.investigation_plan = out.plan
        else:
            s.investigation_plan = ["Explore repository structure", "Search for endpoint/error symbols", "Inspect relevant implementation and tests", "Form an evidence-backed hypothesis"]
        self.store.save(s)
        return _pack(s)

    def investigate(self, gs: GraphState) -> dict[str, Any]:
        s = _model(gs)
        ctx = ToolContext(Path(s.workspace_path))
        tools = build_tools(ctx)
        if self.llm.enabled:
            llm = self.llm.with_tools(tools)
            messages: list[Any] = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"Bug: {s.bug_description}\nPlan: {s.investigation_plan}\nStack trace: {s.stack_trace or 'none'}\nUse repository tools to gather evidence. Make at most 6 tool calls, then summarize what you learned."}]
            for _ in range(6):
                response = llm.invoke(messages)
                messages.append(response)
                calls = getattr(response, "tool_calls", [])
                if not calls:
                    if response.content:
                        s.evidence.append(Evidence(source="agent_summary", detail=str(response.content)[:4000]))
                    break
                for call in calls:
                    tool = next((t for t in tools if t.name == call["name"]), None)
                    if not tool:
                        continue
                    start = time.perf_counter()
                    try:
                        result = tool.invoke(call["args"])
                        success = True
                    except Exception as exc:
                        result = {"error": str(exc)}
                        success = False
                    duration = (time.perf_counter() - start) * 1000
                    s.tool_calls.append(ToolCallRecord(name=call["name"], arguments=call["args"], result=result, success=success, duration_ms=duration))
                    messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result, default=str)[:12000]})
        else:
            for name, args in [("list_files", {"path": "."}), ("search_code", {"query": "orders"}), ("search_code", {"query": "quantity"})]:
                start = time.perf_counter()
                try:
                    if name == "list_files": result = ctx.list_files(__import__('src.tools.repository_tools', fromlist=['ListFilesInput']).ListFilesInput(**args))
                    else: result = ctx.search_code(__import__('src.tools.repository_tools', fromlist=['SearchCodeInput']).SearchCodeInput(**args))
                    success = True
                except Exception as exc: result, success = {"error": str(exc)}, False
                s.tool_calls.append(ToolCallRecord(name=name, arguments=args, result=result, success=success, duration_ms=(time.perf_counter()-start)*1000))
                s.evidence.append(Evidence(source=name, detail=json.dumps(result, default=str)[:5000]))
        # Track files discovered from tool results.
        for tc in s.tool_calls:
            if tc.name in {"read_file", "search_code", "find_references"}:
                text = json.dumps(tc.result, default=str)
                for token in text.split('"'):
                    if token.endswith(".py") or ".py:" in token:
                        s.files_inspected.append(token.split(":")[0])
        s.files_inspected = list(dict.fromkeys(s.files_inspected))
        self.store.save(s)
        return _pack(s)

    def hypothesis(self, gs: GraphState) -> dict[str, Any]:
        s = _model(gs)
        evidence = "\n".join(f"- {e.source}: {e.detail}" for e in s.evidence[-12:])
        if self.llm.enabled:
            structured = self.llm.llm.with_structured_output(HypothesisOutput)
            out = structured.invoke([{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"Bug: {s.bug_description}\nEvidence:\n{evidence}\nPrior test failures:\n{[r.stderr[-3000:] for r in s.test_results[-3:]]}\nGive evidence-backed hypotheses and select one."}])
            s.hypotheses = [Hypothesis(statement=h, confidence=0.8 if h == out.selected_hypothesis else 0.5, evidence=out.evidence) for h in out.hypotheses]
            s.current_hypothesis = out.selected_hypothesis
        else:
            s.current_hypothesis = "The relevant endpoint or validation path does not correctly handle the zero-quantity edge case; inspect the quantity calculation and its tests."
            s.hypotheses = [Hypothesis(statement=s.current_hypothesis, confidence=0.5, evidence=[e.detail[:500] for e in s.evidence[-3:]])]
        self.store.save(s)
        return _pack(s)

    def patch(self, gs: GraphState) -> dict[str, Any]:
        s = _model(gs)
        evidence = "\n".join(f"{e.source}: {e.detail}" for e in s.evidence[-10:])
        failures = "\n".join(r.stderr[-4000:] for r in s.test_results[-3:])
        if not self.llm.enabled:
            if self.settings.demo_mode:
                patch = self._demo_patch(s)
                if patch:
                    PatchManager(Path(s.workspace_path)).validate_and_apply(patch)
                    s.patch = patch
                    s.patch_applied = True
                    s.test_commands = ["python -m pytest"]
                    s.diff = GitContext(Path(s.workspace_path)).diff()
                    self.store.save(s)
                    return _pack(s)
            raise RuntimeError("Patch generation requires OPENAI_API_KEY. Configure an LLM for real debugging, or set DEMO_MODE=true for the bounded demo fixture.")
        structured = self.llm.llm.with_structured_output(PatchOutput)
        out = structured.invoke([{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"Generate the smallest valid unified git diff for the hypothesis below. Only modify files supported by the evidence. Do not wrap the diff in markdown fences.\nBug: {s.bug_description}\nHypothesis: {s.current_hypothesis}\nEvidence:\n{evidence}\nPrevious failures:\n{failures}"}])
        PatchManager(Path(s.workspace_path)).validate_and_apply(out.unified_diff)
        s.patch = out.unified_diff
        s.patch_applied = True
        s.test_commands = out.tests or ["python -m pytest"]
        s.diff = GitContext(Path(s.workspace_path)).diff()
        self.store.save(s)
        return _pack(s)

    def _demo_patch(self, s: DebugState) -> str | None:
        # Bounded local development adapter: only handles the shipped zero-quantity demo.
        if "quantity" not in s.bug_description.lower() or "zero" not in s.bug_description.lower():
            return None
        path = Path(s.workspace_path) / "orders.py"
        if not path.exists():
            return None
        old = path.read_text(encoding="utf-8")
        if "100 / quantity" not in old:
            return None
        return """diff --git a/orders.py b/orders.py
index 1111111..2222222 100644
--- a/orders.py
+++ b/orders.py
@@ -1,3 +1,3 @@
 def orders(quantity: int = 1):
-    total = 100 / quantity
+    total = 0 if quantity == 0 else 100 / quantity
     return {"total": total}
"""

    def execute(self, gs: GraphState) -> dict[str, Any]:
        s = _model(gs)
        s.iteration_count += 1
        runner = CommandRunner(Path(s.workspace_path), self.settings.tool_timeout_seconds)
        results: list[TestResult] = []
        for command in s.test_commands[:3]:
            try:
                if self.sandbox.available():
                    result = self.sandbox.run(Path(s.workspace_path), command, self.settings.tool_timeout_seconds)
                else:
                    result = runner.run(command)
                    result.stderr = "Docker unavailable; local isolated workspace fallback used for development.\n" + result.stderr
                results.append(result)
                s.tool_calls.append(ToolCallRecord(name="run_tests", arguments={"command": command}, result=result.model_dump(), success=result.passed, duration_ms=result.duration_ms))
            except (DockerUnavailable, ValueError) as exc:
                results.append(TestResult(command=command, return_code=None, stderr=str(exc), passed=False))
        s.test_results.extend(results)
        self.store.save(s)
        return _pack(s)

    def after_execute(self, gs: GraphState) -> str:
        s = _model(gs)
        if not s.test_results:
            return "failed"
        if all(r.passed for r in s.test_results[-len(s.test_commands or ["x"]):]):
            return "critic"
        if s.iteration_count >= self.settings.max_iterations:
            return "failed"
        return "retry"

    def critic(self, gs: GraphState) -> dict[str, Any]:
        s = _model(gs)
        latest = "\n".join(f"{r.command}: {'PASS' if r.passed else 'FAIL'}\n{r.stderr[-3000:]}" for r in s.test_results[-5:])
        if self.llm.enabled:
            structured = self.llm.llm.with_structured_output(CriticOutput)
            out = structured.invoke([{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"Critique this proposed fix using only evidence. Tests:\n{latest}\nHypothesis: {s.current_hypothesis}\nDiff:\n{s.diff[-10000:]}"}])
            s.evidence.append(Evidence(source="critic", detail=out.summary + (" Concerns: " + "; ".join(out.concerns) if out.concerns else "")))
            if not out.approved and s.iteration_count < self.settings.max_iterations:
                self.store.save(s)
                return _pack(s)
        self.store.save(s)
        return _pack(s)

    def after_critic(self, gs: GraphState) -> str:
        s = _model(gs)
        if s.iteration_count >= self.settings.max_iterations:
            return "report"
        return "report"

    def report(self, gs: GraphState) -> dict[str, Any]:
        s = _model(gs)
        passed = bool(s.test_results) and all(r.passed for r in s.test_results[-len(s.test_commands or ["x"]):])
        s.status = "awaiting_approval" if passed and s.diff else "failed"
        changed = []
        for line in s.diff.splitlines():
            if line.startswith("+++ b/"):
                changed.append(line[6:])
        s.final_report = FinalReport(
            problem=s.bug_description,
            root_cause=s.current_hypothesis or "Not established",
            evidence=[e.detail for e in s.evidence[-10:]],
            files_investigated=list(dict.fromkeys(s.files_inspected)),
            files_changed=list(dict.fromkeys(changed)),
            patch_summary="Generated and validated a minimal patch." if s.patch_applied else "No validated patch generated.",
            tests_executed=[r.command for r in s.test_results],
            test_results=s.test_results,
            iterations=s.iteration_count,
            limitations=["Docker was unavailable during this run; local fallback may not provide equivalent isolation."] if not self.sandbox.available() else [],
            recommendation="Review the diff and approve only after confirming the change matches the intended product behavior." if passed else "Investigate the remaining failures before approving.",
        )
        self.store.save(s)
        return _pack(s)
