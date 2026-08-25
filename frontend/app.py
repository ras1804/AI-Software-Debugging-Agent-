import time
from pathlib import Path

import requests
import streamlit as st

API = st.sidebar.text_input("API URL", "http://localhost:8000")
st.set_page_config(page_title="AI Software Debugger", layout="wide")
st.title("AI Software Debugger")
st.caption("Agentic repository investigation → sandboxed tests → human approval")

repo = st.text_input("Repository path", str(Path("examples/buggy_orders_app").resolve()))
bug = st.text_area("Bug description", "The /orders endpoint returns HTTP 500 when quantity is zero.")
stack = st.text_area("Stack trace (optional)")

if st.button("Start debugging", type="primary"):
    try:
        r = requests.post(f"{API}/debug", json={"repository_path": repo, "bug_description": bug, "stack_trace": stack or None}, timeout=10)
        r.raise_for_status()
        st.session_state.task_id = r.json()["task_id"]
    except Exception as exc:
        st.error(str(exc))

task_id = st.session_state.get("task_id")
if task_id:
    st.subheader(f"Task {task_id[:8]}")
    for _ in range(1):
        try:
            status = requests.get(f"{API}/debug/{task_id}/status", timeout=5).json()
            st.write(f"**Status:** {status['status']} · **Iterations:** {status['iteration_count']}")
            if status.get("error"):
                st.error(status["error"])
        except Exception as exc:
            st.warning(str(exc))
    if st.button("Refresh"):
        st.rerun()
    if st.button("Load report"):
        st.session_state.report = requests.get(f"{API}/debug/{task_id}/report", timeout=10).json()
        st.session_state.diff = requests.get(f"{API}/debug/{task_id}/diff", timeout=10).json().get("diff", "")
    report = st.session_state.get("report")
    if report and report.get("problem"):
        st.subheader("Debugging report")
        st.write("**Root cause:**", report["root_cause"])
        st.write("**Evidence:**")
        for item in report["evidence"]:
            st.write("-", item)
        st.write("**Files changed:**", report["files_changed"])
        st.write("**Tests:**")
        for result in report["test_results"]:
            st.write(result["command"], "PASS" if result["passed"] else "FAIL")
        st.code(st.session_state.get("diff", ""), language="diff")
        c1, c2 = st.columns(2)
        if c1.button("APPROVE"):
            st.success(requests.post(f"{API}/debug/{task_id}/approve", timeout=10).json()["status"])
        if c2.button("REJECT"):
            st.warning(requests.post(f"{API}/debug/{task_id}/reject", timeout=10).json()["status"])
