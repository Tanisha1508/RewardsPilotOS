"""One test module's worth of table-driven cases per shipped seed card.

Shipped seed files carry null/unverified numerics (no fabricated data), so
the required behavior everywhere is REFUSAL: status 'unknown' with reasons,
never a computed number. Exclusions (non-numeric) still apply.
"""

import pytest

from rules.engine.engine import RuleEngine
from rules.parser.loader import load_rule
from rules.validators.schema import validate_rule_dict

import json
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parents[2] / "rules" / "seed"


@pytest.fixture()
def engine() -> RuleEngine:
    return RuleEngine()  # real seed dir, in-memory cap store


CARD_TABLE = [
    # (card_key, category, channel, expected_status, reason_fragment)
    ("hdfc_infinia", "electronics", None, "unknown", "base earn rate is unverified"),
    ("hdfc_infinia", "flights", "smartbuy", "unknown", "base earn rate is unverified"),
    ("hdfc_infinia", "fuel", None, "excluded", "excluded from earning"),
    ("hdfc_infinia", "rent", None, "excluded", "excluded from earning"),
    ("hdfc_infinia", "wallet_loads", None, "excluded", "excluded from earning"),
    ("axis_atlas", "grocery", None, "unknown", "base earn rate is unverified"),
    ("axis_atlas", "travel", "direct", "unknown", "base earn rate is unverified"),
    ("amex_plat_travel", "dining", None, "unknown", "base earn rate is unverified"),
    ("amex_plat_travel", "travel", "direct", "unknown", "base earn rate is unverified"),
]


@pytest.mark.parametrize("card_key,category,channel,status,fragment", CARD_TABLE)
def test_seed_cards_refuse_unverified(engine, card_key, category, channel, status, fragment):
    result = engine.calculate_earn(card_key, 10_000, category, channel, "2026-07")
    assert result.status == status
    assert result.points is None or result.points == 0.0
    assert any(fragment in reason for reason in result.unknown_reasons)
    if status == "unknown":
        assert result.points is None, "unknown must never carry a number"


@pytest.mark.parametrize("card_key", ["hdfc_infinia", "axis_atlas", "amex_plat_travel"])
def test_seed_files_are_schema_valid(card_key):
    raw = json.loads((SEED_DIR / card_key / "v1.json").read_text())
    assert validate_rule_dict(raw) == []
    rule = load_rule(card_key)
    assert rule.card_key == card_key


@pytest.mark.parametrize("card_key", ["hdfc_infinia", "axis_atlas", "amex_plat_travel"])
def test_seed_files_contain_no_fabricated_numbers(card_key):
    """Every verified-value struct in shipped seeds must be null + unverified
    until real issuer verification happens (tracked in VERIFICATION_QUEUE)."""
    raw = json.loads((SEED_DIR / card_key / "v1.json").read_text())

    def walk(node):
        if isinstance(node, dict):
            if "status" in node and "confidence" in node:
                assert node["status"] == "unverified"
                assert node["value"] is None
                assert node["confidence"] == 0
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(raw)


@pytest.mark.parametrize("card_key", ["hdfc_infinia", "axis_atlas"])
def test_seed_cap_checks_are_unknown(engine, card_key):
    scope = "smartbuy_total" if card_key == "hdfc_infinia" else "travel_accelerated"
    status = engine.check_cap(card_key, scope, "2026-07")
    assert status.status == "unknown"
    assert status.remaining_points is None


def test_compare_seed_cards_all_unknown(engine):
    results = engine.compare_cards(
        ["hdfc_infinia", "axis_atlas", "amex_plat_travel"], 70_000, "electronics", None, "2026-07"
    )
    assert all(r.status == "unknown" for r in results)
    assert all(r.points is None for r in results)
