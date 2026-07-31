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


# Every category word the rule files and this module actually use — both sides
# of the alias map and both sides of the subsumption map. Used only to answer
# "have we ever seen this word before?" (B2, KNOWN_LIMITATIONS 30).
RECOGNISED_CATEGORIES: frozenset[str] = (
    frozenset(CATEGORY_ALIASES)
    | frozenset(CATEGORY_ALIASES.values())
    | frozenset(CATEGORY_SUBSUMES)
    | frozenset().union(*CATEGORY_SUBSUMES.values())
)


def unrecognised_category_note(card_key: str, category: str, bonus_categories: list[str]) -> str:
    """Say that a category we do not recognise was scored at base earn.

    The gap this closes (KNOWN_LIMITATIONS 30): an unmapped category silently
    earns base, which is *correct* for genuinely different spend ("groceries")
    and *wrong* for an unrecognised synonym of a bonus category. `hotel` for
    `hotels` cost a 10x under-report that way — one letter, full confidence, no
    warning. The alias map now covers the variants we thought of, and by
    construction cannot cover the ones we did not.

    So rather than guess, the engine reports what it did and what else exists.
    Deterministic text carrying the card's own declared categories verbatim, so
    the Recommender repeats it without inventing anything.

    Fires only when the card actually has bonus categories to miss — on a card
    with none, base earn is the only possible answer and there is nothing to
    warn about.
    """
    named = ", ".join(sorted(set(bonus_categories)))
    return (
        f"'{category}' is not a spend category any rule file uses, so {card_key} "
        f"was scored at its base rate. This card earns an accelerated rate on: "
        f"{named}. If your spend falls into one of those, say so — the figure "
        f"would change."
    )


def is_recognised_category(category: str, declared: list[str] | None = None) -> bool:
    """True when `category` is a word the rule files use.

    `declared` lets a card's own categories count as recognised even when they
    are absent from both maps here — a rule file is the authority on its own
    vocabulary, and a new issuer must not need this module edited before its
    categories stop being reported as unrecognised."""
    if not category:
        return False
    known = RECOGNISED_CATEGORIES | frozenset(declared or ())
    return canonical_category(category) in known or category in known


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
