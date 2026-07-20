"""Spend-category subsumption for accelerated-earn matching (BUILD_SPEC §5).

Issuers describe the same spend in different granularity. Axis Atlas encodes
its direct accelerated entry as category "travel" because its T&C says "direct
airline and direct hotel bookings, identified via MCC codes"; HDFC Infinia
encodes SmartBuy entries as "flights" and "hotels" separately. Both are
faithful transcriptions of their sources.

Without a declared relationship between them, `compare_cards(..., "flights")`
matched Infinia's entry but not Atlas's, silently returning Atlas's BASE rate
and reporting the wrong card as the winner. Comparison takes one category for
all cards, so this cannot be fixed by the caller.

This map declares only subsumption that the underlying sources state outright:
a rule category matches a queried category when the rule's category is the
same, is "all", or is a broader category that provably contains it. It adds no
rate, cap, or issuer policy — it is a taxonomy, not reward data. Every entry
must be justified by the rule file's own source text.

Discovered 2026-07-20 during end-to-end demo-query testing; see ADR-010.
"""

# broader category -> the narrower categories it provably contains.
# Justification per entry is the issuer source quoted in the rule file.
CATEGORY_SUBSUMES: dict[str, frozenset[str]] = {
    # Axis Atlas: "direct airline and direct hotel bookings" (official
    # 'Atlas Credit Card Features T&Cs' PDF, retrieved 2026-07-19).
    "travel": frozenset({"flights", "hotels"}),
}


def category_matches(rule_category: str, queried_category: str) -> bool:
    """True when an accelerated entry declared for `rule_category` applies to
    spend in `queried_category`. Never widens in the other direction: an entry
    declared for "flights" does NOT apply to a generic "travel" query, because
    the issuer only committed to flights."""
    if rule_category in (queried_category, "all"):
        return True
    return queried_category in CATEGORY_SUBSUMES.get(rule_category, frozenset())
