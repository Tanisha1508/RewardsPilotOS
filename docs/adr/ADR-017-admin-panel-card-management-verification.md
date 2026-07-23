# ADR-017: Admin Panel for Card Management and Rule Verification

## Status

Accepted as a fast-follow (2026-07-21). **Not built.** Deferred until after the
MVP ships (post D5). Documented now so the extension point is designed against
the existing Rule Verifier (ADR-009) rather than bolted on later.

## Context

Card verification today is a **manual pipeline run by one operator through chat
sessions**: research the issuer's official terms, consolidate convergent
sources into verified values, and apply them via a prompt that writes the rule
file and knowledge docs. It has worked — all three P1 cards (HDFC Infinia, Axis
Atlas, Amex Platinum Travel) are fully verified this way, every value carrying a
source and confidence.

Two pressures make that path insufficient past the MVP:

1. **It does not scale past one operator working directly in chat.** Each card
   is a hand-run session. The VERIFICATION_QUEUE has seven P2 cards and a P3
   roadmap beyond them; onboarding a second person, or running verification as a
   repeatable operation rather than a bespoke session, has no home in the
   product.

2. **Some cards' key facts are crawler blind spots, and nothing surfaces
   which.** The crawler detects HTML-level change but cannot read JS-rendered
   detail — Axis's Travel EDGE transfer-partner table, Amex's exact figures and
   MR partner list (KNOWN_LIMITATIONS items 20–21). Those specific facts depend
   on a human remembering to re-check, and nothing in the product tells an
   operator *which* cards are in that position versus fully covered by automated
   detection.

   *(This point originally cited HDFC as fully robots-blocked — the only
   freshness path being manual. That was corrected 2026-07-22: it was a wrong
   URL, not a real block; HDFC is fully crawlable. The blind-spot-visibility
   argument stands on Axis and Amex, and the scaling argument in point 1 never
   depended on HDFC.)*

The crawler (D3) already detects change and the Rule Verifier design (ADR-009)
already defines how a detected change becomes a reviewed, approved rule update
via `pending_review` verification records. What is missing is the **operator
surface** on top of that machinery — and an operator surface implies an
**admin concept the auth system does not have**.

## Decision

Defer building an admin panel until after the MVP ships. When built, it sits
**on top of the existing Rule Verifier (ADR-009), not beside it** — it is the UI
for machinery that already exists, not a second verification system. Scope:

- **Card CRUD at the catalogue level** — issuer, card name, region, product
  family. Distinct from the portfolio `cards` table (a user's *held* cards);
  this is the set of cards the system *knows how to reason about*, i.e. which
  rule files exist and their verification status.
- **A manual "trigger crawl" action per source** — the same crawl the weekly
  cron runs (`knowledge/crawler/crawl.py`), invoked on demand for one source.
  This is the operator's lever for a card the cron cannot cover (HDFC) or when a
  change is suspected before the next scheduled run. `workflow_dispatch` already
  exists at the workflow level; this exposes it per-source in-product.
- **A review UI for `pending_review` verification records** — approve/reject
  against ADR-009's `verification_record.schema.json` (the same
  `card / field / candidate_value / status / confidence / source / extractor`
  shape). Approval re-runs Rule Engine, Graph Engine, and eval benchmarks, per
  ADR-009. Nothing is applied to rule files automatically — the panel is the
  approval gate, not an auto-apply path.
- **A manual "trigger smoke suite run" action** — the live-LLM smoke suite
  (`evaluation/smoke/run.py`), the same run the Mon/Thu Action does, invoked on
  demand; `workflow_dispatch` already exposes it at the workflow level, this
  surfaces it in-product (KNOWN_LIMITATIONS 23–26).
- **Blind-spot visibility per card** — surface which cards carry crawler blind
  spots (KNOWN_LIMITATIONS 20–21: Axis JS-rendered partner table, Amex
  JS-rendered figures) so an operator can tell at a glance which cards need
  **scheduled manual re-checks** versus which are covered by **automated
  detection**. Without this the reaction-delay distinction (items 20–22) lives
  only in docs, not in the tool the operator
  actually uses.

**This requires a new admin role/permission layer the auth system does not
have.** Current auth (D2, ADR-014) is single-user and portfolio-scoped: every
route resolves `current_user_id` from the token and reads only that user's own
data. There is no notion of an operator who acts across cards and approves
verification records — no role claim, no admin route guard, no separation
between "a user managing their portfolio" and "an operator managing the card
catalogue and rule files." That is **new architectural surface area**, not a
small addition, and is the main reason this is a fast-follow rather than a D-series
increment: it touches the identity model, not just a new screen.

## Consequences

**Manual prompt-driven verification remains the only path until this is built.**
That is acceptable for the MVP and the current P1/P2 verification pace — three
P1 cards done, seven P2 cards queued at a deliberate one-card-at-a-time cadence
that a single operator sustains. The cost is that scaling operators, or turning
verification into a repeatable non-chat operation, waits.

**Blind-spot facts stay a human calendar item** (Axis partner table, Amex
figures) until the panel makes "which cards need manual re-checks" visible
in-product. Recorded so it is a known gap, not a surprise (KNOWN_LIMITATIONS
items 20–21).

**When built, it is additive.** It consumes ADR-009's verification records and
the D3 crawler unchanged; the new work is the admin identity layer and the UI,
not new verification logic. Building it earlier would not have changed the P1/P2
data — the machinery underneath is the same.

## Alternatives considered

**Build a minimal admin panel now, inside D4/D5.** Rejected: the auth work
(roles, admin guards, catalogue-vs-portfolio separation) is real architectural
surface area, and the MVP does not need it — one operator in chat sustains the
current pace. Pulling it forward would spend MVP budget on operator ergonomics
before there is a second operator.

**Give the admin panel its own verification pipeline separate from ADR-009.**
Rejected: it would duplicate the verification-record contract and the
approval-re-runs-evals guarantee, and create two ways to change a rule file —
exactly the ambiguity ADR-009 exists to prevent. The panel must be a UI over the
one pipeline, never a second one.

**Bypass the admin concept by keeping verification in chat sessions
permanently.** Rejected as the long-term answer (it is the MVP answer): it does
not scale past one operator, has no audit surface beyond git history, and offers
no in-product view of blind-spot coverage. Fine until the MVP ships; not after.

## References

- ADR-009 — Manual Approval for Rule Verification (the pipeline this panel drives)
- ADR-014 — Supabase asymmetric JWT (the single-user auth this extends)
- ADR-016 — Crawler detects change, does not re-ingest
- KNOWN_LIMITATIONS items 20–22 — crawler blind spots and weekly cadence
- BUILD_SPEC §14a — Fast Follow: Rule Verifier
