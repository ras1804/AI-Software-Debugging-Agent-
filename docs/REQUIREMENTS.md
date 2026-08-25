# Requirements Checklist

## Core workflow
- [x] Python repository + bug description input
- [x] Stack trace / logs input
- [x] Stateful debugging workflow
- [x] Planning
- [x] Repository investigation
- [x] Hypothesis generation
- [x] Patch generation
- [x] Patch validation/application
- [x] Test execution
- [x] Iterative recovery with max iterations
- [x] Verification/critic
- [x] Human approval/rejection
- [x] Structured final report

## Agentic AI
- [x] LLM integration
- [x] Tool calling interface
- [x] Structured outputs
- [x] Typed state
- [x] Tool selection
- [x] Error handling
- [x] Replanning
- [x] No private chain-of-thought exposure

## Repository intelligence
- [x] Ingestion into isolated workspace
- [x] Directory exploration
- [x] File reading
- [x] Code search
- [x] AST reference search
- [x] Git diff
- [x] Test discovery/execution

## Security
- [x] Command allowlist
- [x] Workspace path restriction
- [x] Patch validation
- [x] Docker sandbox implementation
- [x] Timeout
- [x] CPU/memory/PID limits
- [x] Network restriction
- [x] Capability dropping
- [x] Secret isolation
- [~] Full production-grade sandbox hardening requires host/runtime controls

## MLOps / LLMOps
- [x] MLflow integration
- [x] Benchmark version configuration
- [x] Experiment parameters
- [x] Evaluation metrics
- [x] Evaluation artifacts
- [x] Reproducible benchmark runner
- [~] Provider-specific token/cost accounting

## Benchmark
- [x] 10 deterministic tasks
- [x] Varied bug categories
- [x] Known root-cause metadata
- [x] Automated evaluation runner
- [x] Real metric calculation
- [x] Experiment comparison through MLflow runs

## Application
- [x] FastAPI
- [x] Required debug endpoints
- [x] Streamlit UI
- [x] Persistent task state

## Engineering
- [x] Unit tests
- [x] Integration tests
- [~] E2E plumbing test exists; full agent E2E requires runtime dependencies, LLM credentials, and Docker
- [x] Dockerfile
- [x] Docker Compose
- [x] GitHub Actions
- [x] Ruff configuration
- [x] mypy configuration
- [x] Structured logging
- [x] .env.example

## Documentation
- [x] README
- [x] Architecture document
- [x] Decision records
- [x] Mermaid diagrams
- [x] Benchmark README
- [x] Limitations

## Optional
- [ ] RAG: intentionally skipped for MVP; exact repository search is the stronger first-line tool.
- [ ] MCP: intentionally skipped; would duplicate the secure internal tool layer.
- [ ] Cloud deployment: intentionally skipped until local Docker workflow is stable.
