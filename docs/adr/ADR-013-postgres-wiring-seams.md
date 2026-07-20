# ADR-013: How Postgres Reaches the Tools

## Status

Accepted (2026-07-20). Covers the D2 wiring decisions.

## Context

D2 replaces the sprint's in-memory fakes with Postgres behind the *existing*
tool interfaces. The Build Constraints forbid changing tool contracts, and the
Tool Registry's handlers are plain functions with spec'd signatures:

    get_portfolio(args: UserScopedInput) -> GetPortfolioOutput

There is nowhere in that signature to pass a database session or a repository.
Adding a parameter would change a contract; constructing a session inside each
handler would make the functions untestable and give one request several
transactions.

## Decision

**Ambient session, resolved source.** Two seams, both following the shape
`rules/engine/cap_store.py` already established for cap usage — a Protocol with
a real implementation and a fake:

1. `database/postgres/session.py` — `session_scope()` yields the session bound
   to the current context, or opens one against `DATABASE_URL`. The API binds
   one session per request, so a multi-write endpoint is one transaction.
2. `tools/portfolio/source.py` and `tools/memory/source.py` — the data source is
   looked up rather than injected. Postgres is the default.

**No fixture fallback in production code.** An unconfigured database raises;
it does not fall back to seed data. Answering a real question with demo
balances is exactly the fabrication the first hard rule forbids, and unlike an
error it would look like a working system. The seeded fakes exist, but the test
suite and the evaluation harness install them explicitly.

**Fixture data moved to `database/seed/demo_portfolio.json`.** BUILD_SPEC §2
designates `database/seed/` for "graph nodes/edges seed, fixtures". Both the
test suite and the evaluation harness read it, so `tests/` alone would not do —
`evaluation/` importing from `tests/` would be worse.

**An ambient user for tools that load "the caller's own data".**
`RedemptionOptionsInput` documents that omitting `portfolio` makes the tool load
the user's balances itself, but the input carries no user id. Rather than change
the contract, the caller establishes the user for the scope of the request
(`acting_as`). This implements what the contract already claimed; before D2 the
same code path answered from a fixture regardless of who was asking.

**`TEST_DATABASE_URL`, separate from `DATABASE_URL`.** The integration suite
runs migrations up and down, so it creates and drops every table. Falling back
to `DATABASE_URL` would mean one absent-minded `pytest` run against a dev or
production database. The suite skips when the variable is unset — an additive
env var beyond BUILD_SPEC §12, recorded here.

**The migration is generated, not transcribed.** The first migration was
rendered from `Base.metadata` rather than typed out, and
`tests/integration/test_migrations.py` re-checks the two agree using Alembic's
own metadata comparison. Hand-transcribing fifteen tables is a reliable way to
lose one column and find out during a deploy.

## Consequences

**Positive.** Nothing above the tools changed: same handler signatures, same
output schemas, unchanged Planner and Recommender. The rules, graph, and
end-to-end evals still run without a database and still score identically.

**A missing database is now loud.** `/health` reports `not_configured` rather
than green; an authenticated request without a database returns 503, not 500.

**Test suite splits.** 304 tests run everywhere; 28 integration tests skip
unless `TEST_DATABASE_URL` is set. A skipped test proves nothing, so this is
stated in the handoff rather than counted as coverage.

**Fakes must be uninstalled deliberately.** `tests/integration/conftest.py`
resets both sources, because integration tests passing against seeded fakes
while appearing to exercise Postgres is the exact false green this design could
otherwise produce.

## Deferred, not solved

Three schema questions surfaced during wiring and are recorded rather than
patched over — see KNOWN_LIMITATIONS items 16–18 and the [NEED] register:

- `cap_usage` has no `user_id`, so its rows are global.
- `cards` has no `reward_currency`, which the tool contract requires.
- `goals` has no `target_program` / `required_points`, which `RedemptionOptions`
  wants.

Each is a schema change, and the schema is spec'd.

## Alternatives rejected

**Pass a session into every tool handler.** Changes tool contracts, which the
Build Constraints forbid, and would ripple into the Tool Registry, the Planner's
plan format, and every golden eval plan.

**Keep a fixture fallback for when the database is missing.** The system would
appear to work while inventing a portfolio. Failing is the honest behaviour.

**Use SQLite for the integration tests so they always run.** The schema uses
JSONB and Postgres UUIDs, so the tests would be exercising a different schema
from the one that ships — a green suite that proves nothing about production.
Skipping loudly beats passing dishonestly.
