# ADR-006: Single sequential tool-executor node

Status: accepted (2026-07-19)

## Context

BUILD_SPEC §8 describes "planner → (conditional) tool nodes → recommender".
Per-category LangGraph nodes (portfolio node, rules node, …) need routing
bookkeeping that is not part of the published AgentState schema, and the
state schema is a binding contract we must not extend unilaterally.

## Decision

One `tools` node executes the Planner's validated plan sequentially, in plan
order, dispatching each ToolInvocation through the Tool Registry and
appending results to the category-appropriate state channels (rule_results,
graph_results, knowledge, portfolio, memory). The conditional edge from the
Planner routes to `tools` when a plan exists, straight to `recommender`
otherwise. Tool wrappers stay thin and deterministic; failures append to
`errors` and execution continues.

## Alternatives considered

- Per-category nodes with conditional routing between them — rejected for the
  sprint: requires cursor/bookkeeping fields beyond the published AgentState
  contract; no behavioral difference for sequential deterministic tools.
- Parallel tool execution — deferred: tools are fast on fixtures; parallelism
  adds failure-ordering complexity before it adds user value.

## Consequences

- Flow shape is preserved (conditional edge exists; tool layer is thin,
  deterministic, degradation-tolerant); state schema stays exactly per spec.
- If D4 needs per-category nodes (e.g., for streaming progress), the executor
  can be split without touching tool wrappers or contracts — the plan format
  already carries the category via the registry.
