# Architecture

## Boundaries

1. **API layer** accepts requests and exposes task state.
2. **Service layer** owns task lifecycle and persistence.
3. **Agent layer** owns the LangGraph state machine and LLM interactions.
4. **Tool layer** performs bounded repository/Git/test operations.
5. **Sandbox layer** isolates untrusted code execution.
6. **Evaluation layer** executes deterministic benchmark tasks and records metrics.
7. **Observability/MLOps** provides structured logs and MLflow experiment tracking.

## State

`DebugState` is a typed Pydantic model. It is persisted after meaningful transitions so a task can be inspected without reconstructing an opaque conversation.

## Agentic behavior

The agent explicitly plans, chooses investigation tools, accumulates evidence, forms hypotheses, generates a patch, executes tests, and routes test failures back to hypothesis generation until a configured iteration limit is reached.

The real LLM path uses native LangChain tool binding for repository tools. The patch is not accepted until `git apply --check` succeeds and tests validate it.

## Trust model

Repository contents are untrusted. The host-side repository tooling is read-oriented except for the isolated workspace patch. Arbitrary commands are not exposed. Test execution should use Docker in production mode. The current development implementation has a local fallback only so the API remains testable on machines without Docker; the final report explicitly records that limitation.

## Persistence

SQLite is used because the expected workload is a portfolio project with a small number of concurrent tasks. SQLAlchemy keeps the persistence layer replaceable.
