"""A wording variant must not silently cost the bonus rate (found live 2026-07-29).

The Planner emitted `category: "hotel"`; every rule file says "hotels". Nothing
matched, so HDFC Infinia's smartbuy/hotels entry was skipped and the query
scored base earn. One letter, 10x wrong, no warning.

Same family as ADR-010 and ADR-011 — the model's words and the rule files' words
disagreeing — but on a third axis, and a wider one: `category` is free text with
no vocabulary at all behind it.

Aliasing happens at the tool boundary, so these tests go through the tools rather
than the engine: that is the seam the fix lives on, and testing the engine
directly would pass whether or not it is wired up.
"""

from contracts.tools.rule_engine import CalculateEarnInput, CompareCardsInput
from rules.evaluator.categories import canonical_category
from tools.rule_engine.tools import calculate_earn, compare_cards


def _earn(category: str, channel: str | None = "smartbuy", card: str = "hdfc_infinia"):
    return calculate_earn(
        CalculateEarnInput(
            card_key=card, amount=30000, category=category, channel=channel, month="2026-07"
        )
    )


def test_the_live_regression_singular_hotel_now_earns_the_bonus():
    """The exact defect: 1,000 vs 10,000 points on a SmartBuy hotel booking."""
    singular = _earn("hotel")
    plural = _earn("hotels")

    assert singular.points == plural.points == 10000.0
    assert singular.applied == plural.applied == "accelerated"


def test_the_category_is_echoed_back_canonicalised():
    """`EarnResult.category` feeds the answer the user reads. Echoing the raw
    input would show "hotel" beside a rate sourced for "hotels"."""
    assert _earn("hotel").category == "hotels"
    assert _earn("Hotels").category == "hotels"
    assert _earn(" gift cards ").category == "brand_vouchers"


def test_case_spacing_and_hyphens_are_normalised():
    for variant in ("HOTEL", "Hotel", " hotel ", "hotel"):
        assert canonical_category(variant) == "hotels"
    assert canonical_category("gift-cards") == "brand_vouchers"
    assert canonical_category("air travel") == "flights"


def test_a_missed_exclusion_is_covered_too():
    """Worse than a missed bonus: it reports earning on spend that earns nothing.

    Infinia excludes "fuel"; a user asking about "petrol" must get the exclusion,
    not base earn."""
    petrol = _earn("petrol", channel=None)

    assert petrol.status == "excluded"
    assert petrol.points == 0.0
    assert _earn("fuel", channel=None).status == "excluded"


def test_an_unknown_category_passes_through_and_earns_base():
    """Not every category is in the map, and that is correct — "groceries" is a
    real query that legitimately earns base. Rewriting it would be guessing."""
    groceries = _earn("groceries", channel=None)

    assert groceries.status == "computed"
    assert groceries.applied == "base"
    assert groceries.category == "groceries"


def test_comparison_applies_aliasing_to_every_card():
    """CompareCards takes ONE category for all cards, so a missed alias skews the
    ranking rather than just one row."""
    singular = compare_cards(
        CompareCardsInput(
            cards=["hdfc_infinia", "axis_atlas", "amex_plat_travel"],
            amount=30000,
            category="hotel",
            channel="smartbuy",
            month="2026-07",
        )
    ).results
    plural = compare_cards(
        CompareCardsInput(
            cards=["hdfc_infinia", "axis_atlas", "amex_plat_travel"],
            amount=30000,
            category="hotels",
            channel="smartbuy",
            month="2026-07",
        )
    ).results

    assert [r.card_key for r in singular] == [r.card_key for r in plural]
    assert [r.points for r in singular] == [r.points for r in plural]
    assert singular[0].card_key == "hdfc_infinia"
    assert singular[0].points == 10000.0
