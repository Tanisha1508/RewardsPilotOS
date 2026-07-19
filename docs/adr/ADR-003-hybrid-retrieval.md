# ADR-003: Hybrid retrieval (semantic + BM25 + metadata filter + RRF + freshness)

Status: accepted (2026-07-19)

## Context

Reward-program queries mix semantic intent ("can I move points to Singapore
Airlines?") with exact terms that must match literally (card names, program
names, "SmartBuy", ratios). Content freshness matters: a 2024 promotion is
noise in 2026.

## Decision

Five-stage pipeline (`knowledge/retrieval/hybrid.py`): ChromaDB semantic
top-10 (all-MiniLM-L6-v2) + BM25 keyword top-10 over the same corpus +
issuer/program/doc_type metadata filters inferred by the Planner + reciprocal
rank fusion (k=60) + freshness multiplier (half-life 180 days, floor 0.5) on
`last_changed`. Top 5 chunks returned with metadata; citations flow verbatim.

## Alternatives considered

- Semantic-only — rejected: misses exact program/card token matches on a
  domain full of proper nouns.
- BM25-only — rejected: fails paraphrased intent queries.
- Learned reranker (cross-encoder) — deferred: heavier dependency and latency
  for marginal gain at this corpus size; revisit post-MVP.
- LLM re-rank — rejected: nondeterministic, cost per query, evaluation churn.

## Consequences

- Deterministic, offline-testable retrieval with measured metrics
  (REPORT.md); no external services beyond local ChromaDB.
- BM25 index is in-memory and rebuilt on ingest — fine at corpus scale,
  revisit if corpus grows by orders of magnitude.
- Freshness floor 0.5 keeps stale-but-relevant policy docs findable.
