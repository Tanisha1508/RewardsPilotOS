"""Accelerated-earn validity windows (ADR-012).

This closes the one case where the engine could compute with a rate it had no
right to use: a lapsed program whose end date lived only in `notes` prose. The
regression that matters is dated — Amex's Reward Multiplier ends 2026-07-31,
so a query in August must return base earn with an expiry note, not 3X.

Failure class: time-dependent data that the code cannot see because it lives
in a comment. The test that catches it has to move the clock, which no
same-day unit test ever does.
"""

import pytest

from agents.recommendation.calibration import confidence_basis
from contracts.api.verified_value import VerifiedValue
from rules.engine.engine import RuleEngine
from rules.evaluator.validity import boundary_note, is_active, lapse_note, month_status
from rules.parser.models import AcceleratedEarn, RuleFile
from rules.validators.schema import _check_validity_window, validate_rule_dict


def entry(valid_from=None, valid_until=None) -> AcceleratedEarn:
    return AcceleratedEarn(
        channel="reward_multiplier",
        category="all",
        multiplier=VerifiedValue(value=3, status="verified", source="t&c", confidence=0.95),
        valid_from=valid_from,
        valid_until=valid_until,
    )


# --- window arithmetic -------------------------------------------------


def test_entry_without_dates_is_always_active():
    """Cards whose programs publish no window must behave exactly as before
    the change — this is what keeps the other two P1 cards unaffected."""
    assert is_active(entry(), "1970-01")
    assert is_active(entry(), "2099-12")
    assert lapse_note(entry(), "2099-12") is None


def test_final_month_of_the_window_is_still_active():
    """A program ending 2026-07-31 applies for all of July: the engine works
    in months, and the window overlaps that month."""
    assert is_active(entry(valid_until="2026-07-31"), "2026-07")


def test_month_after_expiry_is_inactive():
    assert not is_active(entry(valid_until="2026-07-31"), "2026-08")
    assert not is_active(entry(valid_until="2026-07-31"), "2027-01")


def test_month_before_start_is_inactive():
    assert not is_active(entry(valid_from="2021-01-01"), "2020-12")
    assert is_active(entry(valid_from="2021-01-01"), "2021-01")


def test_open_ended_sides_are_unbounded():
    assert is_active(entry(valid_from="2021-01-01"), "2099-01")
    assert is_active(entry(valid_until="2026-07-31"), "1999-01")


# --- mid-month boundary (KNOWN_LIMITATIONS 10) ------------------------


def test_a_clean_month_end_is_active_not_boundary():
    """A window ending on the last day of the month covers the whole month —
    the Amex case (2026-07-31) must stay 'active', not regress to boundary."""
    assert month_status(entry(valid_until="2026-07-31"), "2026-07") == "active"


def test_expiry_partway_through_a_month_is_a_boundary_not_active():
    """The fix: a window ending mid-month only partly covers it, so applying the
    accelerated rate to the whole month would over-credit. That month is a
    boundary (→ unknown), never active."""
    e = entry(valid_until="2026-07-15")
    assert month_status(e, "2026-07") == "boundary"
    assert not is_active(e, "2026-07")
    assert month_status(e, "2026-06") == "active"  # fully-covered month before
    assert month_status(e, "2026-08") == "inactive"  # cleanly past


def test_start_partway_through_a_month_is_a_boundary_too():
    e = entry(valid_from="2026-07-16")
    assert month_status(e, "2026-07") == "boundary"
    assert month_status(e, "2026-08") == "active"


def test_boundary_note_names_the_partial_date_and_says_unknown():
    note = boundary_note(entry(valid_until="2026-07-15"), "2026-07")
    assert "2026-07-15" in note
    assert "2026-07" in note
    assert "unknown" in note
    # and it is None on a cleanly-covered month
    assert boundary_note(entry(valid_until="2026-07-31"), "2026-07") is None


def test_lapse_note_names_the_expiry_date_and_asks_for_reverification():
    note = lapse_note(entry(valid_until="2026-07-31"), "2026-08")
    assert "2026-07-31" in note
    assert "2026-08" in note
    assert "base earn" in note
    assert "re-verify" in note


def test_lapse_note_distinguishes_not_yet_started_from_expired():
    note = lapse_note(entry(valid_from="2027-01-01"), "2026-08")
    assert "does not start until" in note
    assert "expired" not in note


# --- rule-file validation ---------------------------------------------


def test_malformed_validity_date_is_a_schema_violation():
    """String comparison means a garbage date fails silently rather than
    loudly — it would make an entry permanently active or permanently
    lapsed. Catch it at the file level instead."""
    problems = validate_rule_dict(
        {
            "card_key": "x",
            "version": 1,
            "effective_date": "2026-01-01",
            "reward_currency": "pts",
            "base_earn": {
                "rate": {"value": 1, "status": "verified", "source": "s", "confidence": 0.9},
                "per_amount": 50,
                "currency": "INR",
            },
            "accelerated": [
                {
                    "channel": "portal",
                    "category": "all",
                    "multiplier": {
                        "value": 3,
                        "status": "verified",
                        "source": "s",
                        "confidence": 0.9,
                    },
                    "valid_until": "31-07-2026",
                }
            ],
        }
    )
    assert any("valid_until" in p and "ISO date" in p for p in problems)


def test_reversed_validity_window_is_a_schema_violation():
    problems = _check_validity_window(
        {"valid_from": "2026-08-01", "valid_until": "2026-07-31"}, "accelerated[0]"
    )
    assert any("is after" in p for p in problems)


def test_absent_or_open_ended_dates_are_valid():
    assert _check_validity_window({}, "accelerated[0]") == []
    assert _check_validity_window({"valid_from": "2021-01-01"}, "accelerated[0]") == []


def test_seed_files_pass_validation():
    """The Amex file now carries real dates — it must still validate."""
    import json
    from pathlib import Path

    path = Path("rules/seed/amex_plat_travel/v3.json")
    assert validate_rule_dict(json.loads(path.read_text())) == []


# --- the dated regression ---------------------------------------------


@pytest.fixture
def engine():
    return RuleEngine()


def test_amex_reward_multiplier_applies_through_july_2026(engine):
    """Baseline: 3X is in force in the program's final month."""
    result = engine.calculate_earn(
        "amex_plat_travel", 50_000, "hotels", "reward_multiplier", "2026-07"
    )
    assert result.status == "computed"
    assert result.applied == "accelerated"
    assert result.multiplier.value == 3
    assert result.expiry_note is None
    # floor(50000/50) = 1000 blocks * rate 1 * 3
    assert result.points == 3000.0


def test_amex_reward_multiplier_does_not_apply_from_august_2026(engine):
    """The regression this ADR exists for: after 2026-07-31 the engine must
    fall back to base earn rather than keep applying a lapsed 3X."""
    result = engine.calculate_earn(
        "amex_plat_travel", 50_000, "hotels", "reward_multiplier", "2026-08"
    )

    assert result.status == "computed"
    assert result.applied == "base"
    assert result.multiplier is None
    assert result.points == 1000.0  # 1000 blocks * rate 1, no multiplier
    assert result.expiry_note is not None
    assert "2026-07-31" in result.expiry_note
    assert "re-verify" in result.expiry_note


def test_expiry_survives_into_later_months(engine):
    result = engine.calculate_earn(
        "amex_plat_travel", 50_000, "hotels", "reward_multiplier", "2027-03"
    )
    assert result.applied == "base"
    assert result.expiry_note is not None


def test_expired_rate_changes_the_comparison_honestly(engine):
    """Amex ranks lower once its multiplier lapses — but it stays in the
    comparison carrying the reason, rather than silently dropping out."""
    july = engine.compare_cards(
        ["hdfc_infinia", "axis_atlas", "amex_plat_travel"],
        50_000,
        "hotels",
        "issuer_portal",
        "2026-07",
    )
    august = engine.compare_cards(
        ["hdfc_infinia", "axis_atlas", "amex_plat_travel"],
        50_000,
        "hotels",
        "issuer_portal",
        "2026-08",
    )

    amex_july = next(r for r in july if r.card_key == "amex_plat_travel")
    amex_august = next(r for r in august if r.card_key == "amex_plat_travel")

    assert amex_august.points < amex_july.points
    assert amex_august.expiry_note is not None
    assert {r.card_key for r in august} == {"hdfc_infinia", "axis_atlas", "amex_plat_travel"}
    # the other two cards are untouched by Amex's expiry
    for card in ("hdfc_infinia", "axis_atlas"):
        assert (
            next(r for r in july if r.card_key == card).points
            == next(r for r in august if r.card_key == card).points
        )


def test_lapsed_rate_caps_reported_confidence(engine):
    """A lapsed rate computes cleanly from a verified base rate, so nothing
    else in calibration would notice it. It must still pull the ceiling down:
    the figure may understate the card if the program was renewed."""
    result = engine.calculate_earn(
        "amex_plat_travel", 50_000, "hotels", "reward_multiplier", "2026-08"
    )
    basis = confidence_basis([{"tool": "CalculateEarn", **result.model_dump()}], [], [])

    assert basis["ceiling"] == "medium"
    assert "lapsed" in basis["reason"]


# --- the dated mid-month regression (KNOWN_LIMITATIONS 10) -------------


def _rule_with_window(valid_from=None, valid_until=None) -> RuleFile:
    """A minimal, self-contained rule: 1 pt / ₹100 base, a 3X accelerated entry
    on the given window. Synthetic — no seed file needed, and dated so the test
    can move the clock past a mid-month boundary."""

    def verified(v):
        return VerifiedValue(value=v, status="verified", source="t&c", confidence=0.95)

    return RuleFile(
        card_key="synthetic_boundary_card",
        version=1,
        effective_date="2021-01-01",
        reward_currency="synthetic_points",
        base_earn={"rate": verified(1), "per_amount": 100, "currency": "INR"},
        accelerated=[
            AcceleratedEarn(
                channel="reward_multiplier",
                category="all",
                multiplier=verified(3),
                valid_from=valid_from,
                valid_until=valid_until,
            )
        ],
    )


def test_mid_month_expiry_returns_unknown_not_over_applied():
    """The core fix. The window ends 2026-07-15, partway through July. The
    engine works at month granularity and cannot split the month, so it must
    return UNKNOWN for July — never the whole-month 3X figure, which would
    over-credit spend made after the 15th (the wrong error direction)."""
    from rules.evaluator.evaluator import evaluate_earn

    rule = _rule_with_window(valid_from="2021-01-01", valid_until="2026-07-15")
    result = evaluate_earn(rule, 50_000, "shopping", "reward_multiplier", "2026-07")

    assert result.status == "unknown"
    assert result.points is None  # emphatically NOT 3000 (the over-applied figure)
    assert any("2026-07-15" in reason for reason in result.unknown_reasons)
    assert any("unknown" in reason for reason in result.unknown_reasons)


def test_month_fully_inside_the_window_still_applies_the_rate():
    """June is fully covered by a window ending 2026-07-15, so it computes 3X
    normally — the fix must not make covered months unknown."""
    from rules.evaluator.evaluator import evaluate_earn

    rule = _rule_with_window(valid_from="2021-01-01", valid_until="2026-07-15")
    result = evaluate_earn(rule, 50_000, "shopping", "reward_multiplier", "2026-06")

    assert result.status == "computed"
    assert result.applied == "accelerated"
    assert result.points == 1500.0  # floor(50000/100)=500 blocks * 1 * 3


def test_month_after_a_mid_month_expiry_falls_to_base_cleanly():
    """August is entirely past the 2026-07-15 window: cleanly lapsed, so it is
    base earn with an expiry note — the ADR-012 path, not the boundary path."""
    from rules.evaluator.evaluator import evaluate_earn

    rule = _rule_with_window(valid_from="2021-01-01", valid_until="2026-07-15")
    result = evaluate_earn(rule, 50_000, "shopping", "reward_multiplier", "2026-08")

    assert result.status == "computed"
    assert result.applied == "base"
    assert result.points == 500.0
    assert result.expiry_note is not None


# --- overlapping-window validation (KNOWN_LIMITATIONS 10) --------------


def _accel(channel, category, valid_from=None, valid_until=None) -> dict:
    node = {
        "channel": channel,
        "category": category,
        "multiplier": {"value": 3, "status": "verified", "source": "t&c", "confidence": 0.95},
    }
    if valid_from:
        node["valid_from"] = valid_from
    if valid_until:
        node["valid_until"] = valid_until
    return node


def test_overlapping_windows_same_channel_category_are_rejected():
    """Two entries on the same channel/category whose windows overlap would
    resolve to whichever is listed first — a load-time error, not a silent
    first-wins."""
    raw = {
        "accelerated": [
            _accel("reward_multiplier", "all", "2021-01-01", "2026-07-31"),
            _accel("reward_multiplier", "all", "2026-07-01", None),  # overlaps July
        ]
    }
    problems = validate_rule_dict(raw)
    assert any("overlapping validity windows" in p for p in problems)


def test_two_undated_entries_on_the_same_key_are_rejected():
    """Both 'always active' on the same channel/category is an unresolvable
    authoring error."""
    raw = {
        "accelerated": [
            _accel("reward_multiplier", "all"),
            _accel("reward_multiplier", "all"),
        ]
    }
    assert any("overlapping validity windows" in p for p in validate_rule_dict(raw))


def test_adjacent_windows_for_a_rate_change_are_allowed():
    """The intended use: a mid-window rate change expressed as two adjacent,
    non-overlapping windows must pass — the whole point of the schema support."""
    raw = {
        "accelerated": [
            _accel("reward_multiplier", "all", "2021-01-01", "2026-06-30"),
            _accel("reward_multiplier", "all", "2026-07-01", None),
        ]
    }
    assert not any("overlapping" in p for p in validate_rule_dict(raw))


def test_overlap_across_different_categories_is_fine():
    """Different category (or channel) → different rule → no conflict, even with
    identical windows."""
    raw = {
        "accelerated": [
            _accel("smartbuy", "flights", "2021-01-01", None),
            _accel("smartbuy", "hotels", "2021-01-01", None),
        ]
    }
    assert not any("overlapping" in p for p in validate_rule_dict(raw))
