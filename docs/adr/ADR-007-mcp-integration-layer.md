# ADR-007: MCP as a separate external-integration layer, stubs first

Status: accepted (2026-07-19)

## Context

The system will eventually need live issuer pages, browser automation,
email/calendar access, and travel search. Mixing external integrations into
the internal tool registry blurs the line between deterministic business
logic and unreliable external I/O.

## Decision

External capabilities live behind MCP clients (`mcp/clients/`) speaking the
contracts in `contracts/mcp/`. Routing rule: internal tools for business
logic and computation; MCP only for external capabilities or live
information. Sprint ships the common base contract plus Browser/Playwright
stubs returning typed `pending_integration` errors and four interface-only
clients (Email, Calendar, FlightSearch, HotelSearch). Real servers are wired
only if the final day finishes early (roadmap-flagged).

## Alternatives considered

- Direct httpx/Playwright calls inside tools — rejected: entangles retries,
  auth, and rate limits with deterministic logic; untestable offline.
- Skipping MCP entirely until needed — rejected: the Planner's routing rule
  and error contracts must exist now so downstream code is written against
  them.
- Wiring one live server in the sprint — rejected: scope; typed pending
  errors exercise the same code paths.

## Consequences

- The Planner can already reason about MCP unavailability (structured
  errors: reduce confidence, use indexed knowledge, inform the user).
- Adding a real server is an implementation of an existing interface, not a
  redesign. Secrets stay per-server, never in the LLM context.
