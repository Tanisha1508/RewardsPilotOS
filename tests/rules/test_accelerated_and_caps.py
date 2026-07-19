"""Accelerated earn, cap boundaries, and unverified-cap refusal paths.

Fixture card v2: base rate 3 per 100 INR; smartbuy/flights multiplier 5 with a
4000-point monthly cap (scope smartbuy_total). ₹10,000 spend → 100 blocks →
300 base points → 1500 accelerated points.
"""

import pytest

from rules.engine.cap_store import InMemoryCapUsageStore
from rules.engine.engine import RuleEngine


@pytest.fixture()
def store() -> InMemoryCapUsageStore:
    return InMemoryCapUsageStore()


@pytest.fixture()
def engine(fixture_seed_dir, store) -> RuleEngine:
    return RuleEngine(cap_store=store, seed_dir=fixture_seed_dir)


def test_accelerated_computed_under_cap(engine):
    result = engine.calculate_earn("test_voyager", 10_000, "flights", "smartbuy", "2026-07")
    assert result.status == "computed"
    assert result.applied == "accelerated"
    assert result.points == 1500.0
    assert result.points_before_cap == 1500.0
    assert result.cap_applied is False
    assert result.cap_scope == "smartbuy_total"
    assert len(result.sources) == 3  # rate + multiplier + cap


def test_accelerated_cap_boundary_clips(engine, store):
    store.record("test_voyager", "smartbuy_total", "2026-07", 3800.0)
    result = engine.calculate_earn("test_voyager", 10_000, "flights", "smartbuy", "2026-07")
    assert result.status == "computed"
    assert result.points == 200.0  # remaining cap
    assert result.points_before_cap == 1500.0
    assert result.cap_applied is True


def test_accelerated_cap_reached_earns_zero(engine, store):
    store.record("test_voyager", "smartbuy_total", "2026-07", 4000.0)
    result = engine.calculate_earn("test_voyager", 10_000, "flights", "smartbuy", "2026-07")
    assert result.points == 0.0
    assert result.cap_applied is True


def test_cap_is_per_month(engine, store):
    store.record("test_voyager", "smartbuy_total", "2026-06", 4000.0)
    result = engine.calculate_earn("test_voyager", 10_000, "flights", "smartbuy", "2026-07")
    assert result.points == 1500.0
    assert result.cap_applied is False


def test_unverified_multiplier_refuses(engine):
    result = engine.calculate_earn("test_voyager", 10_000, "hotels", "smartbuy", "2026-07")
    assert result.status == "unknown"
    assert result.points is None
    assert "multiplier" in result.unknown_reasons[0]


def test_category_all_matches_and_uncapped(engine):
    result = engine.calculate_earn("test_voyager", 10_000, "anything", "portal", "2026-07")
    assert result.status == "computed"
    assert result.points == 900.0  # 300 base * 3, no cap declared
    assert result.cap_applied is False
    assert result.cap_scope is None


def test_cap_scope_fallback_to_channel_category(engine, store):
    result = engine.calculate_earn("test_voyager", 10_000, "grocery", "store", "2026-07")
    assert result.status == "computed"
    assert result.cap_scope == "store_grocery"
    assert result.points == 600.0  # 300 * 2, cap 1000 not binding


def test_unverified_nonnull_cap_refuses(engine):
    result = engine.calculate_earn("test_voyager", 10_000, "dining", "rumor", "2026-07")
    assert result.status == "unknown"
    assert result.points is None
    assert "monthly cap" in result.unknown_reasons[0]


def test_check_cap_ok(engine, store):
    store.record("test_voyager", "smartbuy_total", "2026-07", 1000.0)
    status = engine.check_cap("test_voyager", "smartbuy_total", "2026-07")
    assert status.status == "ok"
    assert status.accrued_points == 1000.0
    assert status.remaining_points == 3000.0
    assert status.sources


def test_check_cap_reached(engine, store):
    store.record("test_voyager", "smartbuy_total", "2026-07", 4500.0)
    status = engine.check_cap("test_voyager", "smartbuy_total", "2026-07")
    assert status.status == "reached"
    assert status.remaining_points == 0.0


def test_check_cap_unverified_is_unknown(engine):
    status = engine.check_cap("test_voyager", "unverified_cap", "2026-07")
    assert status.status == "unknown"
    assert status.remaining_points is None
    assert "cannot compute" in status.unknown_reasons[0]


def test_check_cap_missing_scope_is_unknown(engine):
    status = engine.check_cap("test_voyager", "no_such_scope", "2026-07")
    assert status.status == "unknown"
    assert "no cap with scope" in status.unknown_reasons[0]
