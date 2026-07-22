"""Shared fixtures for Rule Engine tests.

`test_voyager` is a SYNTHETIC fixture card (source URLs under example.test).
It exists so verified-value computation paths can be exercised without
shipping fabricated real-issuer numbers. Real seed files (hdfc_infinia,
axis_atlas, amex_plat_travel) ship nulls and are tested for refusal paths.
"""

import json
from pathlib import Path

import pytest

SYNTH = "https://example.test/voyager-terms"


def vv(value=None, status="unverified", source=None, confidence=0.0):
    return {"value": value, "status": status, "source": source, "confidence": confidence}


def verified(value, source=SYNTH, confidence=0.9):
    return vv(value, "verified", source, confidence)


def nested_point_value(**channels):
    reference = {"cashback": vv(), "voucher": vv(), "travel": vv()}
    reference.update(channels)
    return reference


def make_rule(**overrides):
    rule = {
        "card_key": "test_voyager",
        "version": 1,
        "effective_date": "2026-01-01",
        "reward_currency": "voyager_points",
        "base_earn": {"rate": verified(2), "per_amount": 100, "currency": "INR"},
        "accelerated": [],
        "caps": [],
        "exclusions": [],
        "milestones": [],
        "point_value_reference_inr": nested_point_value(),
    }
    rule.update(overrides)
    return rule


VOYAGER_V1 = make_rule(
    accelerated=[
        {
            "channel": "smartbuy",
            "category": "flights",
            "multiplier": verified(5),
            "monthly_cap_points": verified(4000),
            "cap_scope": "smartbuy_total",
            "notes": "synthetic fixture",
        },
        {
            "channel": "smartbuy",
            "category": "hotels",
            "multiplier": vv(),
            "monthly_cap_points": vv(),
            "cap_scope": "smartbuy_total",
            "notes": "unverified multiplier: refusal path",
        },
        {
            "channel": "portal",
            "category": "all",
            "multiplier": verified(3),
            "monthly_cap_points": vv(),
            "cap_scope": None,
            "notes": "no cap declared: uncapped accelerated earn",
        },
        {
            "channel": "store",
            "category": "grocery",
            "multiplier": verified(2),
            "monthly_cap_points": verified(1000),
            "cap_scope": None,
            "notes": "cap without explicit scope: falls back to channel_category",
        },
        {
            "channel": "rumor",
            "category": "dining",
            "multiplier": verified(4),
            "monthly_cap_points": vv(value=500),
            "cap_scope": "rumor_scope",
            "notes": "unverified non-null cap value: refusal path",
        },
    ],
    caps=[
        {"scope": "smartbuy_total", "period": "month", "cap_points": verified(4000)},
        {"scope": "unverified_cap", "period": "month", "cap_points": vv()},
    ],
    exclusions=["fuel"],
    point_value_reference_inr=nested_point_value(voucher=verified(0.5), travel=verified(0.5)),
)

VOYAGER_V2 = {
    **VOYAGER_V1,
    "version": 2,
    "effective_date": "2026-06-01",
    "base_earn": {"rate": verified(3), "per_amount": 100, "currency": "INR"},
}


@pytest.fixture(scope="session")
def fixture_seed_dir(tmp_path_factory) -> Path:
    seed = tmp_path_factory.mktemp("seed")
    card = seed / "test_voyager"
    card.mkdir()
    (card / "v1.json").write_text(json.dumps(VOYAGER_V1))
    (card / "v2.json").write_text(json.dumps(VOYAGER_V2))
    (card / "notes.txt").write_text("not a rule version file")
    empty = seed / "test_empty"
    empty.mkdir()
    (empty / "readme.md").write_text("no versions here")
    return seed
