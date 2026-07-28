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


# Wording variant -> the vocabulary the rule files actually use.
#
# Found live 2026-07-29: the Planner emitted `category: "hotel"` where every
# rule file says "hotels". Nothing matched, so HDFC Infinia's smartbuy/hotels
# entry was skipped and a Rs 30,000 SmartBuy hotel booking scored 1,000 points
# instead of 10,000 — a 10x under-report, silent, from one letter.
#
# CATEGORY_SUBSUMES answers "does this broader category contain that narrower
# one" and needs an issuer source per entry. This map answers a different and
# much smaller question: "are these two strings the same word?" It must contain
# ONLY spelling and inflection variants — plurals, regional spellings, obvious
# synonyms for the identical concept.
#
# It must never encode a semantic relationship. "petrol" -> "fuel" belongs here
# because they name one thing; "dining" -> "travel" would not, because that is a
# claim about what an issuer rewards, which is CATEGORY_SUBSUMES' job and needs
# a source. Widening this map is how invented issuer policy would get in.
CATEGORY_ALIASES: dict[str, str] = {
    # accelerated-earn vocabulary
    "hotel": "hotels",
    "flight": "flights",
    "airfare": "flights",
    "air_travel": "flights",
    "voucher": "brand_vouchers",
    "vouchers": "brand_vouchers",
    "brand_voucher": "brand_vouchers",
    "gift_card": "brand_vouchers",
    "gift_cards": "brand_vouchers",
    # exclusion vocabulary — a missed exclusion is worse than a missed bonus:
    # it reports earning on spend that earns nothing at all.
    "petrol": "fuel",
    "diesel": "fuel",
    "utility": "utilities",
    "wallet_load": "wallet_loads",
    "cash_transaction": "cash_transactions",
    "government_payment": "government_payments",
    "jewellery": "gold_jewellery",
    "jewelry": "gold_jewellery",
    "gold_jewelry": "gold_jewellery",
}


def canonical_category(category: str) -> str:
    """Map a category to the wording the rule files use.

    Applied at the tool boundary so everything downstream — accelerated
    matching, exclusion checks, and the category echoed back in `EarnResult` —
    sees one vocabulary. Unknown categories pass through unchanged: "groceries"
    is a perfectly valid query that simply earns base, and rewriting it would be
    guessing.
    """
    if not category:
        return category
    key = category.strip().lower().replace(" ", "_").replace("-", "_")
    return CATEGORY_ALIASES.get(key, key)


def category_matches(rule_category: str, queried_category: str) -> bool:
    """True when an accelerated entry declared for `rule_category` applies to
    spend in `queried_category`. Never widens in the other direction: an entry
    declared for "flights" does NOT apply to a generic "travel" query, because
    the issuer only committed to flights."""
    if rule_category in (queried_category, "all"):
        return True
    return queried_category in CATEGORY_SUBSUMES.get(rule_category, frozenset())
