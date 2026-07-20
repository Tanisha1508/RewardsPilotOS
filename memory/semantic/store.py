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
    with session_scope() as session:
        rows = session.scalars(select(Preference).where(Preference.user_id == user_id))
        return {row.key: row.value for row in rows}


def set_preference(user_id: uuid.UUID, key: str, value: str) -> None:
    """Upsert one key. The unique constraint on (user_id, key) makes the
    read-then-write safe against duplicates rather than merely unlikely."""
    with session_scope() as session:
        existing = session.scalars(
            select(Preference).where(Preference.user_id == user_id, Preference.key == key)
        ).first()
        if existing is None:
            session.add(Preference(user_id=user_id, key=key, value=value))
        else:
            existing.value = value
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
