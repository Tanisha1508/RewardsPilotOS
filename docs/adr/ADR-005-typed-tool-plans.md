# ADR-005: LangGraph orchestration with typed ToolInvocation plans

Status: accepted (2026-07-19)

## Context

The Planner must translate free-text queries into tool executions. Free-form
"agent scratchpad" outputs are unparseable, unvalidatable, and let prompt
drift silently change behavior.

## Decision

The Planner emits `list[ToolInvocation]` — `{tool: exact registry name,
args: dict}` — and nothing else. Every entry is validated against the
Pydantic input schema in `contracts/tools/` before entering the state;
malformed entries are rejected and logged to `errors`. LangGraph flow:
`planner → (conditional) tools → recommender → END`, 1 retry with backoff per
LLM node, no retries for deterministic tools, tool failures degrade
gracefully (append to errors, continue).

## Alternatives considered

- ReAct-style free-form loop — rejected: unbounded LLM calls, unvalidated
  actions, nondeterministic cost.
- Native Gemini function-calling — viable, but a JSON plan keeps the contract
  provider-agnostic (single env var model swap) and trivially testable.
- Static per-intent pipelines without an LLM planner — rejected: kills
  flexibility across mixed queries; kept as the deterministic eval harness.

## Consequences

- Plans are auditable and replayable; eval golden plans reuse the same
  validation path as live planning.
- A hallucinated tool name cannot execute anything — it is dropped with a
  logged error.
- Tool schema changes are caught at the contract boundary, not at runtime
  depth.
