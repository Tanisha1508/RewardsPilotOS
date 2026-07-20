"""The existing tool contracts, now served from Postgres.

The point of D2 is that nothing above these tools changed: same handler
signatures, same output schemas, different storage. So these tests call the
tools exactly as the Tool Registry does and validate against the contract
models — if a query returns something the contract cannot represent, the
Planner and Recommender would be the ones to find out.
"""

import uuid

import pytest

from backend.application import goals as goals_service
from backend.application import portfolio as portfolio_service
from backend.application.users import sync_user
from contracts.tools.memory import RecallMemoryInput, StorePreferenceInput
from contracts.tools.portfolio import UserScopedInput
from memory.episodic.store import record_event
from rules.engine.cap_store import PostgresCapUsageStore
from tools.memory.tools import recall_memory, store_preference
from tools.portfolio.source import UnknownUserError
from tools.portfolio.tools import (
    get_cards,
    get_portfolio,
    get_reward_balances,
    get_travel_goals,
)


@pytest.fixture()
def seeded_user(user_id):
    sync_user(user_id, "user@example.test", "Test User")
    card = portfolio_service.add_card(
        user_id, issuer="hdfc", card_name="HDFC Infinia", network="visa", annual_fee=12500.0
    )
    portfolio_service.set_balance(user_id, card.card_id, "hdfc_reward_points", 48000)
    goals_service.create_goal(user_id, "trip", "Award flight on Skyhigh Airways")
    return user_id


def test_get_portfolio_returns_contract_shape(seeded_user):
    output = get_portfolio(UserScopedInput(user_id=str(seeded_user)))
    assert output.user_id == str(seeded_user)
    assert [c.card_name for c in output.cards] == ["HDFC Infinia"]
    assert output.cards[0].annual_fee == 12500.0


def test_get_cards_and_balances_agree_on_card_ids(seeded_user):
    cards = get_cards(UserScopedInput(user_id=str(seeded_user))).cards
    balances = get_reward_balances(UserScopedInput(user_id=str(seeded_user))).balances
    assert {b.card_id for b in balances} <= {c.card_id for c in cards}
    assert balances[0].current_balance == 48000


def test_travel_goals_surface_unknown_rather_than_guessing(seeded_user):
    """`goals` has no target_program or required_points column (BUILD_SPEC §4).
    Parsing them out of the description would be inventing data; the contract
    fields stay None until the schema carries them."""
    goals = get_travel_goals(UserScopedInput(user_id=str(seeded_user))).goals
    assert len(goals) == 1
    assert goals[0].target_program is None
    assert goals[0].required_points is None


def test_unknown_user_raises_rather_than_returning_an_empty_portfolio(user_id):
    """An empty portfolio and an unknown user are different answers. Conflating
    them would let a recommendation be built for nobody."""
    with pytest.raises(UnknownUserError):
        get_portfolio(UserScopedInput(user_id=str(user_id)))


def test_non_uuid_user_id_is_rejected():
    with pytest.raises(UnknownUserError):
        get_cards(UserScopedInput(user_id="fixture_user"))


def test_preferences_round_trip_through_the_tools(seeded_user):
    store_preference(
        StorePreferenceInput(user_id=str(seeded_user), key="home_airport", value="DEL")
    )
    recalled = recall_memory(
        RecallMemoryInput(user_id=str(seeded_user), intent="transfer", query="airport")
    )
    assert recalled.preferences["home_airport"] == "DEL"


def test_store_preference_updates_rather_than_duplicating(seeded_user):
    for value in ("DEL", "BOM"):
        store_preference(
            StorePreferenceInput(user_id=str(seeded_user), key="home_airport", value=value)
        )
    recalled = recall_memory(
        RecallMemoryInput(user_id=str(seeded_user), intent="transfer", query="airport")
    )
    assert recalled.preferences == {"home_airport": "BOM"}


def test_episodic_recall_is_most_recent_first_and_limited(seeded_user):
    for index in range(4):
        record_event(seeded_user, "search", {"query": f"q{index}"})
    recalled = recall_memory(
        RecallMemoryInput(user_id=str(seeded_user), intent="history", query="", limit=2)
    )
    assert len(recalled.episodic) == 2
    assert recalled.episodic[0].payload["query"] == "q3"


def test_cap_usage_accrues_and_reads_back():
    store = PostgresCapUsageStore()
    assert store.get_accrued("hdfc_infinia", "smartbuy_total", "2026-07") == 0.0
    store.record("hdfc_infinia", "smartbuy_total", "2026-07", 4000)
    store.record("hdfc_infinia", "smartbuy_total", "2026-07", 1500)
    assert store.get_accrued("hdfc_infinia", "smartbuy_total", "2026-07") == 5500.0
    # Different month is a different counter — caps reset monthly.
    assert store.get_accrued("hdfc_infinia", "smartbuy_total", "2026-08") == 0.0


def test_cap_usage_absent_row_is_zero_not_unknown():
    """Nothing accrued is genuinely zero: accrual starts at zero each month by
    definition, so this is one of the few places a missing value is knowable."""
    assert PostgresCapUsageStore().get_accrued("axis_atlas", "never_used", "2026-07") == 0.0


def test_rule_engine_reads_cap_usage_from_postgres():
    """The engine's behaviour must not change with the store swapped in — same
    protocol, same numbers."""
    from rules.engine.engine import RuleEngine

    store = PostgresCapUsageStore()
    engine = RuleEngine(cap_store=store)
    before = engine.check_cap("hdfc_infinia", "smartbuy_total", "2026-07")
    store.record("hdfc_infinia", "smartbuy_total", "2026-07", 1000)
    after = engine.check_cap("hdfc_infinia", "smartbuy_total", "2026-07")
    assert after.accrued_points == before.accrued_points + 1000


def test_uuid_users_are_isolated_from_each_other(seeded_user):
    other = uuid.uuid4()
    sync_user(other, "other@example.test", "Other")
    assert get_cards(UserScopedInput(user_id=str(other))).cards == []
    assert len(get_cards(UserScopedInput(user_id=str(seeded_user))).cards) == 1
