# ADR-001: Verified-value structure for every numeric fact

Status: accepted (2026-07-19); amended (2026-07-19, see below)

## Context

Reward rules, transfer ratios, caps, and point values change frequently and
are scattered across issuer pages. An LLM-based system that ships plausible
but unconfirmed numbers gives confidently wrong financial advice — the worst
failure mode for user trust, and decisions (transfers) are irreversible.

## Decision

Every numeric field in rule files, knowledge seeds, and graph edges carries
`{value, status: verified|unverified, source, confidence: 0..1}`
(`contracts/api/verified_value.py`). Invariants enforced at parse time:
unverified ⇒ confidence 0; verified ⇒ non-null value and official source URL.
Engines refuse to compute with anything not verified (`is_usable`) and
surface the result as unknown. Seed data ships `null` + `[NEED: verify from
issuer docs]` flags until verified against issuer sources.

## Alternatives considered

- Ship best-effort numbers from memory/blogs with a disclaimer — rejected:
  violates "unknown is always preferred over incorrect"; disclaimers do not
  prevent wrong decisions.
- Confidence-weighted use of unverified numbers — rejected: any use of an
  unverified number can still be plainly wrong; binary refusal is auditable.
- Track verification out-of-band (spreadsheet) — rejected: not enforceable in
  code paths; drift guaranteed.

## Consequences

- The sprint system honestly answers "unknown" for all real-card math until
  verification lands (VERIFICATION_QUEUE.md drives that work).
- Every computed number is traceable to a source URL; citations come free.
- Slightly verbose seed files; validators keep them consistent.

## Amendment (2026-07-19, product owner spec update)

Two changes landed with the first real verification batch (HDFC Infinia):

1. **Confidence semantics.** Originally: unverified ⇒ confidence 0. Now: on
   an unverified value, confidence records the strength of the unofficial
   evidence behind a *candidate* value (e.g. 0.5 for a third-party aggregator
   figure) and must stay < 1; verified values require confidence > 0.
   Candidate values may be stored for audit and verification workflows
   (cf. ADR-009 verification records) but **computation gating is
   unchanged**: only status=verified values are usable. Unknown is still
   always preferred over incorrect.
2. **Per-channel point values.** `point_value_reference_inr` became
   `{cashback, voucher, travel}`, each a verified-value structure, because a
   point's rupee value depends on the redemption channel. Redemption
   valuation selects the channel from the goal's `redemption_type`.
