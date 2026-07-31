"""Semantic memory: durable user preferences (MASTER_SPEC ch. 22).

Backed by the `preferences` table. This is the same data the `/preferences`
CRUD endpoints expose and the `StorePreference` tool writes — one store, two
callers, so a preference set through the UI is immediately visible to the
agent and vice versa. Two parallel stores would drift.

Preferences are facts the user stated, not inferences drawn about them. The
agent writes here only through `StorePreference`, and `RecallMemory` reads
rather than appending anything to prompts blindly (contracts/tools/memory.py).
"""

import uuid

from sqlalchemy import select

from backend.models.identity import Preference
from database.postgres.session import session_scope


def get_preferences(user_id: uuid.UUID) -> dict[str, str]:
    """Values only. The shape every engine and prompt already expects — adding
    provenance here would change what reaches the model, and the model has no
    use for who set a preference, only for what it is."""
    with session_scope() as session:
        rows = session.scalars(select(Preference).where(Preference.user_id == user_id))
        return {row.key: row.value for row in rows}


def get_preferences_with_source(user_id: uuid.UUID) -> dict[str, dict[str, str]]:
    """`{key: {"value": ..., "source": ...}}`, for the screen that has to show a
    person which of their settings they chose. Separate from `get_preferences`
    so the LLM path keeps its plain-value shape unchanged."""
    with session_scope() as session:
        rows = session.scalars(select(Preference).where(Preference.user_id == user_id))
        return {row.key: {"value": row.value, "source": row.source} for row in rows}


def set_preference(user_id: uuid.UUID, key: str, value: str, source: str = "user") -> None:
    """Upsert one key. The unique constraint on (user_id, key) makes the
    read-then-write safe against duplicates rather than merely unlikely.

    `source` records who decided this — "user" or "assistant" (B3, 2026-07-31).
    It is overwritten on every write, deliberately: if the user edits a value
    the assistant inferred, it becomes theirs, and the screen should stop
    attributing it to the assistant. Provenance describes the value that is
    there now, not the history of the key.

    Defaulting to "user" is the safe direction. A caller that forgets to say
    understates the assistant's involvement rather than overstating it, and the
    failure mode of the alternative — quietly labelling a person's own setting
    as machine-decided — is the one that would make the screen lie."""
    with session_scope() as session:
        existing = session.scalars(
            select(Preference).where(Preference.user_id == user_id, Preference.key == key)
        ).first()
        if existing is None:
            session.add(Preference(user_id=user_id, key=key, value=value, source=source))
        else:
            existing.value = value
            existing.source = source
        session.flush()


def delete_preference(user_id: uuid.UUID, key: str) -> bool:
    with session_scope() as session:
        existing = session.scalars(
            select(Preference).where(Preference.user_id == user_id, Preference.key == key)
        ).first()
        if existing is None:
            return False
        session.delete(existing)
        return True
