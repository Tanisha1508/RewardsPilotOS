# ADR-010: Spend-Category Subsumption in Accelerated Matching

## Status

Accepted (2026-07-20). Implements a correctness fix found during end-to-end
demo-query testing; flagged for product-owner review because it changes
computed earn values for Axis Atlas.

## Context

Issuers describe the same spend at different levels of granularity, and each
rule file faithfully transcribes its own source:

- **Axis Atlas** declares one accelerated entry with category `travel`,
  because its T&C says "direct airline and direct hotel bookings, identified
  via MCC codes".
- **HDFC Infinia** declares separate `flights` and `hotels` entries, because
  SmartBuy publishes them separately at different multipliers (5X / 10X).

`find_accelerated` matched on `entry.category in (category, "all")` — exact
string equality. `compare_cards` takes a SINGLE category for all cards, so
there is no category string that is correct for every card at once:

- `compare_cards(..., "flights")` matched Infinia's entry but **not** Atlas's,
  silently falling back to Atlas's base rate.
- `compare_cards(..., "travel")` would match Atlas but not Infinia.

The user-visible consequence was a confidently wrong recommendation. Demo
query d1 ("₹50,000 flight, which of my three cards?") ranked HDFC Infinia
first at 1,665 points when Axis Atlas actually earns 2,500 EDGE Miles
(5/₹100 accelerated). The system reported **high** confidence, because every
number it used was individually verified — the defect was in which rule was
selected, not in any value.

This is the failure mode the project's first hard rule exists to prevent:
the output was not "unknown", it was incorrect.

## Decision

Introduce an explicit, one-directional category subsumption map in
`rules/evaluator/categories.py`. An accelerated entry declared for category C
applies to queried category Q when C == Q, C == "all", or C is a broader
category that **provably contains** Q per the issuer's own source text.

Subsumption is deliberately one-directional. An entry declared for `flights`
does NOT match a generic `travel` query, because the issuer committed only to
flights; widening in that direction would invent coverage.

The initial map contains exactly one entry, justified by quoted source text:

    "travel" subsumes {"flights", "hotels"}   # Axis Atlas T&C, direct bookings

## Consequences

**Positive.** Cross-issuer comparison is correct for the flagship "which card
for this purchase" question. The taxonomy is data, reviewable in one place,
and each entry is traceable to an issuer source.

**This is a taxonomy, not reward data.** The map contains no rate, cap,
multiplier, or issuer policy. It cannot change what a card earns for a spend
the issuer already covers; it only fixes which declared entry is selected.
It therefore does not weaken the no-fabricated-data rule.

**Risk: over-matching.** A future entry that claims subsumption the source
does not actually state would silently over-report earn. Mitigation: every
entry requires quoted justification, and the map is reviewed as verification
data, not as code.

**Values changed.** Axis Atlas direct `flights` and `hotels` queries now
return accelerated rather than base earn. No other card's output changes; the
seven P2 skeletons remain unknown, and Infinia direct bookings correctly stay
at base (its accelerated entries are SmartBuy-channel only). Regression cover
is in `tests/rules/test_categories.py`, including the exact d1 comparison.

## Alternatives rejected

**Re-encode Atlas as separate `flights`/`hotels` entries.** Would duplicate
one verified T&C clause into two rule entries that the source does not
separate, drifting the rule file away from a faithful transcription.

**Make the Planner emit per-card categories.** `CompareCards` is one call with
one category by contract (BUILD_SPEC §5/§8); changing that is an API-contract
change, and it would push issuer-taxonomy knowledge into the LLM, which must
not hold reward semantics.

**Return "unknown" on taxonomy mismatch.** Honest but needlessly lossy: the
data is verified and the relationship is stated in the source.
