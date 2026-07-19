"""Table-driven cases per shipped seed card.

hdfc_infinia v2 (2026-07-19) carries verified research data: base earn and
SmartBuy multipliers now COMPUTE, exclusions apply, and only the per-channel
point values remain unverified. axis_atlas and amex_plat_travel still ship
null/unverified numerics, so their required behavior is REFUSAL: status
'unknown' with reasons, never a computed number.
"""

import json
from pathlib import Path

import pytest

from rules.engine.engine import RuleEngine
from rules.parser.loader import load_rule
from rules.validators.schema import validate_rule_dict

SEED_DIR = Path(__file__).resolve().parents[2] / "rules" / "seed"
ALL_CARDS = ["hdfc_infinia", "axis_atlas", "amex_plat_travel"]
UNVERIFIED_CARDS = ["axis_atlas", "amex_plat_travel"]


@pytest.fixture()
def engine() -> RuleEngine:
    return RuleEngine()  # real seed dir, in-memory cap store


REFUSAL_TABLE = [
    ("axis_atlas", "grocery", None, "unknown", "base earn rate is unverified"),
    ("axis_atlas", "travel", "direct", "unknown", "base earn rate is unverified"),
    ("amex_plat_travel", "dining", None, "unknown", "base earn rate is unverified"),
    ("amex_plat_travel", "travel", "direct", "unknown", "base earn rate is unverified"),
]


@pytest.mark.parametrize("card_key,category,channel,status,fragment", REFUSAL_TABLE)
def test_unverified_cards_refuse(engine, card_key, category, channel, status, fragment):
    result = engine.calculate_earn(card_key, 10_000, category, channel, "2026-07")
    assert result.status == status
    assert result.points is None, "unknown must never carry a number"
    assert any(fragment in reason for reason in result.unknown_reasons)


HDFC_TABLE = [
    # 5 RP per ₹150: 10_000 -> 66 blocks -> 330 base points
    ("electronics", None, "computed", 330.0, "base", False),
    # SmartBuy flights 5X: 330 * 5 = 1650, under the 15000 monthly cap
    ("flights", "smartbuy", "computed", 1650.0, "accelerated", False),
    # SmartBuy hotels 10X: 330 * 10 = 3300
    ("hotels", "smartbuy", "computed", 3300.0, "accelerated", False),
    # SmartBuy brand vouchers 5X: 1650, under the 3000 voucher cap
    ("brand_vouchers", "smartbuy", "computed", 1650.0, "accelerated", False),
    ("fuel", None, "excluded", 0.0, None, False),
    ("rent", None, "excluded", 0.0, None, False),
    ("wallet_loads", None, "excluded", 0.0, None, False),
    ("easyemi", None, "excluded", 0.0, None, False),
    ("government_payments", None, "excluded", 0.0, None, False),
    ("education_third_party_apps", None, "excluded", 0.0, None, False),
]


@pytest.mark.parametrize("category,channel,status,points,applied,cap_applied", HDFC_TABLE)
def test_hdfc_infinia_v2_computes(engine, category, channel, status, points, applied, cap_applied):
    result = engine.calculate_earn("hdfc_infinia", 10_000, category, channel, "2026-07")
    assert result.status == status
    assert result.points == points
    assert result.applied == applied
    assert result.cap_applied is cap_applied
    if status == "computed":
        assert result.sources, "computed results must carry sources"
        assert result.rule_version == 2


def test_hdfc_voucher_cap_clips(engine):
    # ₹100,000 vouchers: 666 blocks * 5 * 5 = 16650 > 3000 voucher cap
    result = engine.calculate_earn(
        "hdfc_infinia", 100_000, "brand_vouchers", "smartbuy", "2026-07"
    )
    assert result.points == 3000.0
    assert result.cap_applied is True
    assert result.cap_scope == "smartbuy_voucher"


@pytest.mark.parametrize("card_key", ALL_CARDS)
def test_seed_files_are_schema_valid(card_key):
    for version_file in sorted((SEED_DIR / card_key).glob("v*.json")):
        raw = json.loads(version_file.read_text())
        assert validate_rule_dict(raw) == [], version_file
    rule = load_rule(card_key)
    assert rule.card_key == card_key


@pytest.mark.parametrize("card_key", UNVERIFIED_CARDS)
def test_unverified_seed_files_contain_no_fabricated_numbers(card_key):
    """Cards not yet researched must stay all-null/unverified until real
    issuer verification happens (tracked in VERIFICATION_QUEUE)."""
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


def test_hdfc_v2_verified_fields_carry_sources():
    """Every verified value in the researched card must carry a source and
    confidence > 0; every unverified value must stay unusable."""
    raw = json.loads((SEED_DIR / "hdfc_infinia" / "v2.json").read_text())

    def walk(node):
        if isinstance(node, dict):
            if "status" in node and "confidence" in node:
                if node["status"] == "verified":
                    assert node["value"] is not None
                    assert node["source"]
                    assert node["confidence"] > 0
                else:
                    assert node["confidence"] < 1
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(raw)


def test_hdfc_point_values_remain_unusable(engine):
    """Per-channel point values are unverified estimates: present for audit,
    never computable."""
    rule = load_rule("hdfc_infinia")
    for channel in ("cashback", "voucher", "travel"):
        assert rule.point_value_reference_inr.for_channel(channel).is_usable is False


def test_hdfc_cap_check_now_verified(engine):
    status = engine.check_cap("hdfc_infinia", "smartbuy_total", "2026-07")
    assert status.status == "ok"
    assert status.remaining_points == 15000.0


def test_axis_cap_check_still_unknown(engine):
    status = engine.check_cap("axis_atlas", "travel_accelerated", "2026-07")
    assert status.status == "unknown"
    assert status.remaining_points is None


def test_compare_seed_cards_hdfc_computes_others_unknown(engine):
    results = engine.compare_cards(
        ["hdfc_infinia", "axis_atlas", "amex_plat_travel"], 70_000, "electronics", None, "2026-07"
    )
    assert [r.status for r in results] == ["computed", "unknown", "unknown"]
    assert results[0].card_key == "hdfc_infinia"
    assert results[0].points == 2330.0  # floor(70000/150)=466 blocks * 5
    assert all(r.points is None for r in results[1:])
