"""Spend-category subsumption in accelerated matching (ADR-010).

Regression cover for the cross-issuer comparison defect found 2026-07-20:
issuers encode the same spend at different granularity (Axis "travel" vs HDFC
"flights"/"hotels"), and CompareCards takes ONE category for all cards, so
without declared subsumption a direct flight silently fell back to Atlas's
base rate and named the wrong winner.
"""

from rules.engine.engine import RuleEngine
from rules.evaluator.categories import category_matches


def test_exact_and_all_still_match():
    assert category_matches("flights", "flights") is True
    assert category_matches("all", "anything") is True


def test_broader_category_subsumes_narrower():
    assert category_matches("travel", "flights") is True
    assert category_matches("travel", "hotels") is True


def test_subsumption_is_one_directional():
    """An entry declared for "flights" must NOT apply to a generic "travel"
    query — the issuer only committed to flights."""
    assert category_matches("flights", "travel") is False
    assert category_matches("hotels", "travel") is False


def test_unrelated_categories_do_not_match():
    assert category_matches("travel", "grocery") is False
    assert category_matches("dining", "flights") is False


def test_atlas_direct_flight_earns_accelerated_not_base():
    """Axis Atlas encodes direct airline/hotel bookings as category "travel".
    A direct ₹50,000 flight must earn the accelerated 5/₹100 = 2,500 EDGE
    Miles, not the 1,000 base-rate miles reported before the fix."""
    result = RuleEngine().calculate_earn("axis_atlas", 50_000, "flights", "direct", "2026-07")
    assert result.status == "computed"
    assert result.applied == "accelerated"
    assert result.points == 2500.0


def test_atlas_direct_hotel_earns_accelerated():
    result = RuleEngine().calculate_earn("axis_atlas", 20_000, "hotels", "direct", "2026-07")
    assert result.status == "computed"
    assert result.applied == "accelerated"
    assert result.points == 1000.0  # floor(20000/100)=200 blocks x 2 x 2.5


def test_infinia_direct_flight_stays_base():
    """Infinia's accelerated entries are SmartBuy-only; a direct booking must
    not pick up an accelerated rate through subsumption."""
    result = RuleEngine().calculate_earn("hdfc_infinia", 50_000, "flights", "direct", "2026-07")
    assert result.status == "computed"
    assert result.applied == "base"
    assert result.points == 1665.0


def test_cross_issuer_comparison_names_the_right_winner():
    """The d1 demo query: a ₹50,000 direct flight across the three P1 cards.
    Atlas must rank first."""
    results = RuleEngine().compare_cards(
        ["hdfc_infinia", "axis_atlas", "amex_plat_travel"],
        50_000,
        "flights",
        "direct",
        "2026-07",
    )
    assert results[0].card_key == "axis_atlas"
    assert results[0].points == 2500.0
