
import streamlit as st
from app.agent import run_debug

st.set_page_config(page_title="AI Debugging Agent")
st.title("AI Software Debugging Agent")
st.caption("LangGraph + Docker sandbox + MLflow-ready evaluation")

repo = st.text_input("Python repository path", placeholder=r"C:\projects\my-repo")
bug = st.text_area("Bug description")
stack = st.text_area("Optional stack trace")
test_cmd = st.text_input("Test command", "pytest -q")

if st.button("Start debugging"):
    if not repo or not bug:
        st.error("Repository path and bug description are required.")
    else:
        with st.spinner("Running debugging workflow..."):
            try:
                result = run_debug(repo, bug, stack, test_cmd)
                st.subheader("Root cause")
                st.write(result.get("root_cause", ""))
                st.subheader("Patch")
                st.code(result.get("patch", ""), language="diff")
                st.subheader("Tests")
                st.write(result.get("status"))
                st.code(result.get("test_output", ""))
                if result.get("tests_passed"):
                    st.warning("Tests passed. Human approval is required before accepting the patch.")
                    approved = st.checkbox("I approve this patch")
                    if approved:
                        st.success("Approval recorded for this session. Apply the displayed patch to your own working copy only after review.")
                else:
                    st.info("The agent will re-plan until the iteration limit is reached.")
            except Exception as exc:
                st.error(str(exc))
