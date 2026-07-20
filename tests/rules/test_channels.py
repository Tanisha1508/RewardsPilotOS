"""Canonical channel resolution in accelerated matching (ADR-011).

Regression cover for the cross-issuer channel defect: each issuer names its
own portal differently (SmartBuy / Travel EDGE / Reward Multiplier), and
CompareCards takes ONE channel for all cards, so a portal comparison matched
exactly one card and silently returned base rate for the rest.
"""

from rules.engine.engine import RuleEngine
from rules.evaluator.channels import channel_matches, is_canonical


def test_exact_channel_still_matches():
    assert channel_matches("smartbuy", "smartbuy") is True
    assert channel_matches("direct", "direct") is True


def test_canonical_channel_resolves_to_each_issuer_name():
    for issuer_channel in ("smartbuy", "travel_edge", "reward_multiplier"):
        assert channel_matches(issuer_channel, "issuer_portal") is True


def test_resolution_is_one_directional():
    """Querying one issuer's portal must never match another's — that would
    claim HDFC's SmartBuy rate applies to an Axis booking."""
    assert channel_matches("travel_edge", "smartbuy") is False
    assert channel_matches("smartbuy", "travel_edge") is False


def test_direct_is_not_canonical():
    """`direct` already means the same thing for every issuer."""
    assert is_canonical("direct") is False
    assert is_canonical("issuer_portal") is True
    assert channel_matches("smartbuy", "direct") is False


def test_three_card_portal_comparison_uses_each_cards_own_portal():
    """The bug in one test: a ₹50,000 portal hotel booking must return every
    card's portal-accelerated rate, with no silent base-rate fallback.

    Infinia   floor(50000/150)=333 x 5 = 1665 x 10 = 16,650, clipped to the
              15,000 smartbuy_total monthly cap
    Amex      floor(50000/50)=1000 x 1 = 1000 x 3  =  3,000
    Atlas     floor(50000/100)=500 x 2 =  1000 x 2.5 = 2,500
    """
    results = RuleEngine().compare_cards(
        ["hdfc_infinia", "axis_atlas", "amex_plat_travel"],
        50_000,
        "hotels",
        "issuer_portal",
        "2026-07",
    )
    by_card = {r.card_key: r for r in results}

    assert all(r.status == "computed" for r in results)
    assert all(
        r.applied == "accelerated" for r in results
    ), "no card may silently fall back to base on a portal query"

    assert by_card["hdfc_infinia"].points == 15000.0
    assert by_card["hdfc_infinia"].cap_applied is True
    assert by_card["amex_plat_travel"].points == 3000.0
    assert by_card["axis_atlas"].points == 2500.0

    assert [r.card_key for r in results] == [
        "hdfc_infinia",
        "amex_plat_travel",
        "axis_atlas",
    ]


def test_issuer_specific_channel_still_isolates_one_card():
    """Asking for SmartBuy by name is still a valid, HDFC-only question."""
    results = RuleEngine().compare_cards(
        ["hdfc_infinia", "axis_atlas"], 50_000, "hotels", "smartbuy", "2026-07"
    )
    by_card = {r.card_key: r for r in results}
    assert by_card["hdfc_infinia"].applied == "accelerated"
    assert by_card["axis_atlas"].applied == "base"


def test_card_without_a_portal_falls_back_honestly():
    """A card that genuinely has no portal entry earns base — correct, not a
    matching failure. P2 skeletons stay unknown because their rate is
    unverified, not because of channel resolution."""
    engine = RuleEngine()
    unknown = engine.calculate_earn(
        "hdfc_diners_black", 50_000, "hotels", "issuer_portal", "2026-07"
    )
    assert unknown.status == "unknown"
    assert "not yet verified" in unknown.unknown_reasons[0]
