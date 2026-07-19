# ADR-008: Fixture-first sprint behind production interfaces

Status: accepted (2026-07-19)

## Context

The 12-hour sprint targets the intelligence core only (BUILD_SPEC §14). Real
Postgres/Supabase/Redis wiring and verified issuer data land on later days.
The core must be runnable, testable, and honest today without blocking on
either.

## Decision

Every store is an in-memory fake behind the exact production interface
(CapUsageStore, KnowledgeDocsStore, seed-JSON graph loader mirroring the
graph_nodes/graph_edges schema, fixture portfolio/memory/opportunity tools
behind contracts/tools schemas). Fixture *data* is split by honesty rules:

- Synthetic entities (Demo Bank, Sample Bank, Skyhigh, Grandstay) may carry
  "verified" values sourced to their own clearly-labeled synthetic corpus
  (example.test URLs) — they exercise the computed paths.
- Real entities (HDFC, Axis, Amex, real partner programs) ship null +
  unverified + [NEED] flags only; unverified transfer relationships live in
  the [NEED] register, never as computable edges.

## Alternatives considered

- SQLite as an interim DB — rejected: another wiring layer to replace, no
  honesty gain over typed in-memory fakes.
- Realistic-looking values for real cards "to make the demo nicer" —
  rejected outright: fabricated data is the one unforgivable failure mode.
- Mock the engines themselves in tests — rejected: the engines are the
  product; fakes are only at I/O boundaries.

## Consequences

- D2 replaces fakes with Postgres implementations without touching engine
  or agent code (interfaces already match BUILD_SPEC).
- The demo shows both faces: computed numbers on synthetic data and honest
  "unknown" refusals on real cards.
- The [NEED] register is the single work queue for turning unknowns into
  verified values (docs/VERIFICATION_QUEUE.md).
