# ADR-002: Deterministic engines own all math; the LLM never does arithmetic

Status: accepted (2026-07-19)

## Context

LLMs hallucinate numbers and arithmetic, and reward math (caps, floors,
ratios, milestones) must be exactly right and reproducible. Recommendations
must be auditable after the fact.

## Decision

All numbers flow from the Rule Engine and Graph Engine. The Recommender's
`calculations` array must be deep-equal copies of `rule_results` /
`graph_results` entries; `contracts/api/recommendation.validate_recommendation`
rejects anything else, triggering one retry then a typed failure. Prompts
carry the hard instruction; validation makes it mechanical, not aspirational.

## Alternatives considered

- Trust prompt instructions alone — rejected: unverifiable, drifts with model
  versions.
- Let the LLM do simple arithmetic and spot-check — rejected: spot checks
  miss exactly the long-tail errors that destroy trust.
- Function-calling only (LLM computes nothing, but also writes nothing) —
  partially adopted: tools are planned via typed invocations; the LLM still
  writes prose, which is its actual job.

## Consequences

- Eval can string-match every number in a response to a tool output
  (`evaluation/metrics/e2e_eval.py` does exactly that).
- Recommender failures are typed and visible instead of silently wrong.
- The Rule Engine must stay 100% branch-covered (it is the number authority).
