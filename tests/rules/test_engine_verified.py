"""Table-driven tests for computed paths on the synthetic verified fixture card."""

import pytest

from rules.engine.cap_store import InMemoryCapUsageStore
from rules.engine.engine import RuleEngine
from rules.parser.loader import RuleNotFoundError, load_rule
from rules.versioning.selector import select_version


@pytest.fixture()
def engine(fixture_seed_dir) -> RuleEngine:
    return RuleEngine(cap_store=InMemoryCapUsageStore(), seed_dir=fixture_seed_dir)


EARN_TABLE = [
    # (amount, category, channel, expected_status, expected_points, applied, cap_applied)
    (10_000, "electronics", None, "computed", 300.0, "base", False),  # v2 rate 3/100
    (10_050, "electronics", None, "computed", 300.0, "base", False),  # floor to blocks
    (99, "electronics", None, "computed", 0.0, "base", False),  # below one block
    (10_000, "fuel", None, "excluded", 0.0, None, False),
    (10_000, "electronics", "no_such_channel", "computed", 300.0, "base", False),
]


@pytest.mark.parametrize("amount,category,channel,status,points,applied,cap_applied", EARN_TABLE)
def test_earn_table(engine, amount, category, channel, status, points, applied, cap_applied):
    result = engine.calculate_earn("test_voyager", amount, category, channel, "2026-07")
    assert result.status == status
    assert result.points == points
    assert result.applied == applied
    assert result.cap_applied is cap_applied
    if status == "computed":
        assert result.sources, "computed results must carry sources"


def test_versioning_selects_latest_by_default(engine):
    result = engine.calculate_earn("test_voyager", 10_000, "electronics", None, "2026-07")
    assert result.rule_version == 2


def test_versioning_as_of_date(fixture_seed_dir):
    rule = select_version("test_voyager", as_of_date="2026-03-01", seed_dir=fixture_seed_dir)
    assert rule.version == 1
    rule = select_version("test_voyager", as_of_date="2026-06-01", seed_dir=fixture_seed_dir)
    assert rule.version == 2


def test_versioning_no_effective_version(fixture_seed_dir):
    with pytest.raises(RuleNotFoundError):
        select_version("test_voyager", as_of_date="2025-01-01", seed_dir=fixture_seed_dir)


def test_load_rule_explicit_missing_version(fixture_seed_dir):
    with pytest.raises(RuleNotFoundError):
        load_rule("test_voyager", version=99, seed_dir=fixture_seed_dir)


def test_load_rule_unknown_card(fixture_seed_dir):
    with pytest.raises(RuleNotFoundError):
        load_rule("test_ghost", seed_dir=fixture_seed_dir)


def test_load_rule_card_dir_without_versions(fixture_seed_dir):
    with pytest.raises(RuleNotFoundError):
        load_rule("test_empty", seed_dir=fixture_seed_dir)


def test_compare_cards_sorting(engine):
    results = engine.compare_cards(
        ["test_voyager", "test_ghost"], 10_000, "electronics", None, "2026-07"
    )
    assert [r.card_key for r in results] == ["test_voyager", "test_ghost"]
    assert results[0].status == "computed"
    assert results[1].status == "unknown"
    assert "no rule directory" in results[1].unknown_reasons[0]


def test_compare_cards_excluded_sorts_last(engine):
    results = engine.compare_cards(["test_ghost", "test_voyager"], 10_000, "fuel", None, "2026-07")
    assert [r.status for r in results] == ["unknown", "excluded"]


def test_cap_store_roundtrip():
    store = InMemoryCapUsageStore()
    assert store.get_accrued("c", "s", "2026-07") == 0.0
    store.record("c", "s", "2026-07", 120.0)
    store.record("c", "s", "2026-07", 30.0)
    assert store.get_accrued("c", "s", "2026-07") == 150.0
