"""Proof that source confidence never influences ranking or computed values.

Confidence answers "how well-evidenced is this number", which is a different
question from "how good is this number for the user". Conflating them would
let a well-sourced weak card out-rank a thinly-sourced strong one, which is a
judgement the engine has no basis to make. The engine therefore ranks on
verified computed values ONLY; confidence is reported separately as a
calibration signal on the final answer (agents/recommendation/calibration.py).

Separation point: `VerifiedValue.is_usable` (contracts/api/verified_value.py)
gates computation on `status == "verified" and value is not None`. Confidence
is a sibling field it never consults.
"""

import json

import pytest

from rules.engine.engine import RuleEngine
from tests.rules.conftest import make_rule, verified

SYNTH = "https://example.test/terms"

# Two cards with IDENTICAL earning structure. The only difference anywhere is
# the confidence attached to the sources.
STRONG_SOURCE = make_rule(
    card_key="twin_strong",
    base_earn={"rate": verified(5, SYNTH, confidence=0.95), "per_amount": 100, "currency": "INR"},
    accelerated=[
        {
            "channel": "portal",
            "category": "all",
            "multiplier": verified(3, SYNTH, confidence=0.95),
            "monthly_cap_points": verified(100_000, SYNTH, confidence=0.95),
            "cap_scope": "portal_total",
            "notes": "well-evidenced source",
        }
    ],
    caps=[
        {
            "scope": "portal_total",
            "period": "month",
            "cap_points": verified(100_000, SYNTH, confidence=0.95),
        }
    ],
)

WEAK_SOURCE = {
    **STRONG_SOURCE,
    "card_key": "twin_weak",
    "base_earn": {"rate": verified(5, SYNTH, confidence=0.7), "per_amount": 100, "currency": "INR"},
    "accelerated": [
        {
            "channel": "portal",
            "category": "all",
            "multiplier": verified(3, SYNTH, confidence=0.7),
            "monthly_cap_points": verified(100_000, SYNTH, confidence=0.7),
            "cap_scope": "portal_total",
            "notes": "thinly-evidenced source",
        }
    ],
    "caps": [
        {
            "scope": "portal_total",
            "period": "month",
            "cap_points": verified(100_000, SYNTH, confidence=0.7),
        }
    ],
}

# A card that earns strictly MORE, from a weaker source than the twins. Ranking
# must still put it first: more points wins, regardless of evidence strength.
WEAK_BUT_HIGHER = {
    **WEAK_SOURCE,
    "card_key": "weak_but_higher",
    "accelerated": [
        {
            "channel": "portal",
            "category": "all",
            "multiplier": verified(10, SYNTH, confidence=0.6),
            "monthly_cap_points": verified(100_000, SYNTH, confidence=0.6),
            "cap_scope": "portal_total",
            "notes": "much weaker source, much higher rate",
        }
    ],
}


@pytest.fixture(scope="module")
def twins_seed_dir(tmp_path_factory):
    seed = tmp_path_factory.mktemp("twins")
    for rule in (STRONG_SOURCE, WEAK_SOURCE, WEAK_BUT_HIGHER):
        card = seed / rule["card_key"]
        card.mkdir()
        (card / "v1.json").write_text(json.dumps(rule))
    return seed


@pytest.fixture()
def engine(twins_seed_dir) -> RuleEngine:
    return RuleEngine(seed_dir=twins_seed_dir)


def test_identical_values_different_confidence_compute_identically(engine):
    """Confidence must not weight the computed number: no expected_value =
    points * confidence, no discounting."""
    strong = engine.calculate_earn("twin_strong", 10_000, "shopping", "portal", "2026-07")
    weak = engine.calculate_earn("twin_weak", 10_000, "shopping", "portal", "2026-07")

    assert strong.points == weak.points == 1500.0
    assert strong.status == weak.status == "computed"
    assert strong.points_before_cap == weak.points_before_cap
    # the confidences really do differ — the test is not vacuous
    assert strong.rate.confidence == 0.95
    assert weak.rate.confidence == 0.7


def test_confidence_is_not_a_tiebreaker(engine):
    """Equal points must not be reordered by evidence strength. Sorting is
    stable, so the better-sourced card must NOT be promoted above the
    thinly-sourced one — input order is preserved."""
    weak_first = engine.compare_cards(
        ["twin_weak", "twin_strong"], 10_000, "shopping", "portal", "2026-07"
    )
    assert [r.card_key for r in weak_first] == ["twin_weak", "twin_strong"]
    assert weak_first[0].points == weak_first[1].points

    strong_first = engine.compare_cards(
        ["twin_strong", "twin_weak"], 10_000, "shopping", "portal", "2026-07"
    )
    assert [r.card_key for r in strong_first] == ["twin_strong", "twin_weak"]


def test_weaker_source_with_higher_earn_still_wins(engine):
    """The consequence of the rule, stated plainly: ranking is on points
    alone, so a 0.6-sourced higher rate out-ranks a 0.95-sourced lower one.
    The evidence gap is surfaced through the reported confidence on the final
    answer, never by silently reordering cards."""
    results = engine.compare_cards(
        ["twin_strong", "weak_but_higher"], 10_000, "shopping", "portal", "2026-07"
    )
    assert results[0].card_key == "weak_but_higher"
    assert results[0].points == 5000.0
    assert results[0].multiplier.confidence == 0.6
    assert results[1].card_key == "twin_strong"
    assert results[1].multiplier.confidence == 0.95


def test_low_confidence_is_never_excluded_from_computation(engine):
    """Confidence must not act as a threshold filter. A verified value at 0.6
    computes exactly like one at 0.95 — only `status` gates computation."""
    result = engine.calculate_earn("weak_but_higher", 10_000, "shopping", "portal", "2026-07")
    assert result.status == "computed"
    assert result.points == 5000.0


def test_is_usable_ignores_confidence():
    """The separation point itself: contracts/api/verified_value.py."""
    from contracts.api.verified_value import VerifiedValue

    barely = VerifiedValue(value=5, status="verified", source=SYNTH, confidence=0.01)
    certain = VerifiedValue(value=5, status="verified", source=SYNTH, confidence=1.0)
    assert barely.is_usable is certain.is_usable is True

    # status, not confidence, is what gates computation
    candidate = VerifiedValue(value=5, status="unverified", source="blog", confidence=0.99)
    assert candidate.is_usable is False
