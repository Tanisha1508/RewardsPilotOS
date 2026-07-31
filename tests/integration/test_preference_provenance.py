"""A preference the assistant set must not look like one the user chose
(B3 decision, 2026-07-31).

`preferences` stored key, value and a timestamp. Nothing recorded where a value
came from, so a value the assistant inferred from a conversation and wrote via
`StorePreference` was indistinguishable from one the user typed into the Reward
preferences screen. Since a preference changes what the product recommends,
that is the difference between a setting someone chose and one that was chosen
for them.

Needs the real database: the column is the whole point, and the in-memory fake
deliberately drops `source`.
"""

import uuid

import pytest

from backend.application import preferences as prefs_service
from backend.application.users import sync_user
from memory.semantic.store import get_preferences, get_preferences_with_source, set_preference


@pytest.fixture()
def user(user_id):
    sync_user(user_id, "provenance@example.test", "Provenance")
    return user_id


def test_a_write_through_the_api_is_the_users_own(user):
    prefs_service.write_preferences(user, {"home_airport": "DEL"})
    assert prefs_service.read_preference_sources(user) == {"home_airport": "user"}


def test_a_write_through_the_tool_is_attributed_to_the_assistant(user):
    """The tool hard-codes its source, so this also covers that model output
    cannot claim a write was the user's."""
    from tools.memory.source import PostgresMemorySource, set_source
    from tools.memory.tools import store_preference
    from tools.portfolio.source import acting_as
    from contracts.tools.memory import StorePreferenceInput

    set_source(PostgresMemorySource())
    with acting_as(str(user)):
        store_preference(StorePreferenceInput(key="preferred_airline", value="AI"))

    assert prefs_service.read_preference_sources(user)["preferred_airline"] == "assistant"


def test_editing_an_assistant_value_makes_it_the_users(user):
    """Provenance describes the value that is there now, not the history of the
    key. If a person corrects what the assistant inferred, the screen must stop
    attributing it to the assistant."""
    set_preference(user, "home_airport", "BOM", source="assistant")
    assert prefs_service.read_preference_sources(user)["home_airport"] == "assistant"

    prefs_service.write_preferences(user, {"home_airport": "DEL"})

    assert prefs_service.read_preference_sources(user)["home_airport"] == "user"
    assert get_preferences(user)["home_airport"] == "DEL"


def test_the_engine_facing_reader_is_unchanged(user):
    """`get_preferences` feeds the prompts. Its shape must stay plain values —
    the model has no use for who set a preference, only for what it is."""
    set_preference(user, "home_airport", "DEL", source="assistant")
    assert get_preferences(user) == {"home_airport": "DEL"}


def test_both_are_visible_together(user):
    set_preference(user, "a", "1", source="user")
    set_preference(user, "b", "2", source="assistant")

    assert get_preferences_with_source(user) == {
        "a": {"value": "1", "source": "user"},
        "b": {"value": "2", "source": "assistant"},
    }


def test_existing_rows_default_to_the_user(user):
    """The migration's server default. Every row that existed before the column
    was written through the preferences API by a person, so "user" is the true
    value for them rather than convenient filler."""
    from sqlalchemy import text

    from database.postgres.session import session_scope

    pref_id = uuid.uuid4()
    with session_scope() as session:
        session.execute(
            text(
                "INSERT INTO preferences (pref_id, user_id, key, value, updated_at) "
                "VALUES (:p, :u, 'legacy_key', 'legacy', now())"
            ),
            {"p": pref_id, "u": user},
        )

    assert prefs_service.read_preference_sources(user)["legacy_key"] == "user"
