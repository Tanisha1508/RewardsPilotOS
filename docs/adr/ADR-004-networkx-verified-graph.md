# ADR-004: In-process NetworkX graph with verified-only path computation

Status: accepted (2026-07-19)

## Context

Transfer optimization is a small-graph problem (dozens of nodes, hundreds of
edges at most) needing multi-hop path search with ratio products, minimum
transfer constraints, and strict data provenance.

## Decision

NetworkX DiGraph built by `graph/builder/` from `graph_nodes`/`graph_edges`
records (JSON seed now, Postgres at D2 behind the same `build_graph`
interface). Only verified transfer edges enter path math (subgraph view in
`graph/constraints/`). Unverified transfer relationships live in the [NEED]
register, load as `unverified_transfer` edges, and surface exclusively as
"unverified path exists" notes. The builder hard-fails on unverified ratios
in the verified seed and on ratio values attached to register entries.

## Alternatives considered

- Graph database (Neo4j) — rejected: operational cost, free-tier constraint,
  massive overkill for graph size.
- SQL recursive CTEs — rejected: path ranking with products and constraints
  is awkward and hard to test against hand-computed fixtures.
- Dropping unverified edges entirely — rejected: users deserve to know a
  path may exist; silently hiding it looks like "no options".

## Consequences

- Hand-computed golden paths make graph eval exact-match (10/10).
- Graph rebuilds are cheap; loaded per process, cacheable.
- All-simple-paths enumeration is fine at this scale; bounded by max_hops.
