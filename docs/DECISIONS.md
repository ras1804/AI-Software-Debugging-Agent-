# Architecture Decisions

## ADR-001: LangGraph single-agent workflow

Use one primary debugging agent represented as an explicit state graph. This provides durable, inspectable transitions without the coordination cost of multiple agents.

## ADR-002: Docker sandbox

Treat repository code as untrusted. Execute tests in an ephemeral container with network disabled, limited CPU/memory/PIDs, dropped capabilities, and no-new-privileges.

## ADR-003: SQLite persistence

Use SQLite for the MVP because it is transactional, zero-operations, and sufficient for a local portfolio deployment. SQLAlchemy provides a path to PostgreSQL later.

## ADR-004: Exact repository search first

Do not add a vector database just to claim RAG. Code search and AST references are deterministic and directly relevant to debugging. Documentation retrieval can be added if benchmark results justify it.

## ADR-005: Human approval gate

The agent can reach `awaiting_approval` but cannot mark a task completed by itself. Approval is an explicit API/UI action.

## ADR-006: No fabricated evaluation

The evaluator only records metrics from actual benchmark executions. If an LLM key is absent, patch generation fails safely rather than producing simulated success.

## ADR-007: Python-only scope

Python enables a focused toolchain, predictable test execution, and a realistic one-month implementation boundary.
