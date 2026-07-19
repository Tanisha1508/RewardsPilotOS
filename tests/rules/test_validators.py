"""Table-driven extended-field-schema validator tests."""

import json

import pytest

from rules.parser.loader import RuleValidationError, load_rule
from rules.validators.schema import validate_rule_dict
from tests.rules.conftest import make_rule, verified, vv

VIOLATION_TABLE = [
    # (mutation, expected_fragment)
    (lambda r: r.pop("card_key"), "card_key: required field missing"),
    (lambda r: r.pop("version"), "version: required field missing"),
    (lambda r: r["base_earn"].__setitem__("rate", 5), "must be a verified-value object"),
    (lambda r: r["base_earn"]["rate"].__setitem__("status", "maybe"), "status: must be"),
    (
        lambda r: r["base_earn"]["rate"].__setitem__("confidence", "high"),
        "confidence: must be a number",
    ),
    (
        lambda r: r["base_earn"]["rate"].__setitem__("confidence", 1.5),
        "confidence: must be a number between 0 and 1",
    ),
    (
        lambda r: r.__setitem__("point_value_reference_inr", vv()),
        "flat verified-value structure is obsolete",
    ),
    (
        lambda r: r.__setitem__("point_value_reference_inr", 0.5),
        "must be a per-channel object",
    ),
    (
        lambda r: r["point_value_reference_inr"].pop("travel"),
        "point_value_reference_inr.travel: required channel missing",
    ),
    (
        lambda r: r["point_value_reference_inr"].__setitem__(
            "cashback", vv(value=0.3, confidence=1.0)
        ),
        "unverified values cannot claim full confidence",
    ),
    (
        lambda r: r["base_earn"].__setitem__("rate", {**verified(2), "confidence": 0}),
        "verified values require confidence > 0",
    ),
    (
        lambda r: r["base_earn"].__setitem__("rate", {**verified(2), "value": None}),
        "verified value must not be null",
    ),
    (
        lambda r: r["base_earn"].__setitem__("rate", {**verified(2), "source": None}),
        "requires an official source URL",
    ),
    (lambda r: r["base_earn"].__setitem__("per_amount", 0), "per_amount: must be a positive"),
    (lambda r: r["base_earn"].__setitem__("per_amount", "100"), "per_amount: must be a positive"),
    (
        lambda r: r.__setitem__("accelerated", [{"channel": "x", "category": "y"}]),
        "multiplier: required verified-value field missing",
    ),
    (
        lambda r: r.__setitem__(
            "accelerated",
            [{"channel": "x", "category": "y", "multiplier": vv(), "monthly_cap_points": 100}],
        ),
        "accelerated[0].monthly_cap_points: numeric field must be a verified-value object",
    ),
    (
        lambda r: r.__setitem__("caps", [{"scope": "s", "period": "month", "cap_points": 500}]),
        "caps[0].cap_points",
    ),
    (
        lambda r: r.__setitem__(
            "milestones",
            [{"spend_threshold": vv(), "bonus_points": 8000, "period": "year"}],
        ),
        "milestones[0].bonus_points",
    ),
]


@pytest.mark.parametrize("mutate,fragment", VIOLATION_TABLE)
def test_violations(mutate, fragment):
    rule = json.loads(json.dumps(make_rule()))  # deep copy
    mutate(rule)
    problems = validate_rule_dict(rule)
    assert any(fragment in p for p in problems), problems


def test_valid_rule_passes():
    assert validate_rule_dict(make_rule()) == []


def test_missing_optional_point_value_is_allowed():
    rule = make_rule()
    rule.pop("point_value_reference_inr")
    assert validate_rule_dict(rule) == []


def test_missing_base_earn_reported_once():
    rule = make_rule()
    rule.pop("base_earn")
    problems = validate_rule_dict(rule)
    assert problems == ["base_earn: required field missing"]


def test_loader_rejects_invalid_file(tmp_path):
    card = tmp_path / "test_bad"
    card.mkdir()
    bad = make_rule(card_key="test_bad")
    bad["base_earn"]["rate"] = 5
    (card / "v1.json").write_text(json.dumps(bad))
    with pytest.raises(RuleValidationError):
        load_rule("test_bad", seed_dir=tmp_path)
