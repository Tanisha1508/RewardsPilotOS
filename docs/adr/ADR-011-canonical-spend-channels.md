# ADR-011: Canonical Spend Channels for Cross-Issuer Comparison

## Status

Accepted (2026-07-20). Companion to ADR-010, fixing the same class of defect
on the channel axis.

## Context

ADR-010 fixed cross-issuer matching on the **category** axis but left the
**channel** axis untouched, and the identical defect was still live there.

Each issuer names its own booking portal differently, and each rule file
faithfully records the issuer's own name:

| Issuer | Portal channel |
|---|---|
| HDFC Infinia | `smartbuy` |
| Axis Atlas | `travel_edge` |
| Amex Platinum Travel | `reward_multiplier` |

`CompareCards` takes a SINGLE channel string for all cards. A portal question
therefore matched exactly one card — whichever issuer's portal name happened
to be passed — and every other card silently fell back to its base rate.

Measured on a ₹50,000 portal hotel booking with `channel="smartbuy"`: Axis
Atlas returned 1,000 points (base 2/₹100) instead of the 2,500 its Travel EDGE
rate actually earns. The comparison was not merely imprecise, it was wrong,
and it was wrong silently — every value used was verified and individually
correct.

**Why this survived verification.** Verification and integration are different
failure surfaces. Every rule field passed field-level review because every
rule field *was* correct at the source. Both this bug and ADR-010's live in
the matching layer between a query and the right rule, which no amount of
per-field research can catch. The test that finds them is a cross-card query
exercising each issuer's actual channel and category vocabulary — a different
kind of test from "is this rule field correct".

## Decision

Introduce **canonical channels** in `rules/evaluator/channels.py`: query-side
concepts that resolve to whichever issuer-specific channel each card declares.

    "issuer_portal" -> {smartbuy, travel_edge, reward_multiplier}

`find_accelerated` matches an entry when the rule's channel equals the queried
channel, or when the queried channel is canonical and the rule's channel is
one of its aliases.

Resolution is one-directional. Querying `smartbuy` must never match Axis's
`travel_edge`; that would claim HDFC's portal rate applies to an Axis booking.
Only the canonical name widens.

`direct` is deliberately NOT canonical — it already means the same thing for
every issuer (booking with the merchant rather than through a portal).

The Planner prompt instructs use of `issuer_portal` for generic portal
questions and a specific name only when the user names that portal.

## Consequences

**Positive.** Cross-card portal comparison is correct. The design is
card-agnostic: registering a new issuer's portal name makes every card using
it resolve correctly, with no per-card table to keep in sync — unlike a
per-card channel mapping, which drifts as cards are added.

**This is a vocabulary, not reward data.** It contains no rate, cap, or
multiplier and cannot change what a card earns on a channel the issuer already
covers. The no-fabricated-data rule is unaffected.

**Risk: a wrong alias.** Registering a channel name under the wrong canonical
concept would apply the wrong accelerated entry. Mitigation: each alias must
be a channel an issuer actually declares in its rule file, and the map is
reviewed as verification data rather than as code.

**Values changed.** Only for queries using a canonical channel, which did not
previously resolve at all. Queries naming a specific channel behave exactly as
before, including correctly returning base rate for cards that do not have
that channel. Regression cover in `tests/rules/test_channels.py`, including
the three-card portal comparison that asserts no card falls back to base.

## Alternatives rejected

**Per-card channel mapping in `CompareCards`.** Changes the tool's input
contract (BUILD_SPEC §5/§8) and pushes issuer-taxonomy knowledge into the
caller, which for agent-driven queries means into the LLM. Reward semantics
must not live in the model.

**Rename channels to a shared vocabulary in the rule files.** Would drift each
rule file away from a faithful transcription of its issuer's own terms, and
loses the ability to answer "what does SmartBuy specifically pay?".
