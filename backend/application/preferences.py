"""Preferences endpoints, delegating to semantic memory.

Deliberately thin. The preference store lives in `memory/semantic/` because
preferences *are* the semantic memory layer (MASTER_SPEC ch. 22); duplicating
the queries here would give the UI and the agent two code paths to the same
rows, which is how they drift.
"""

import uuid

from memory.semantic.store import get_preferences, set_preference


def read_preferences(user_id: uuid.UUID) -> dict[str, str]:
    return get_preferences(user_id)


def write_preferences(user_id: uuid.UUID, values: dict[str, str]) -> dict[str, str]:
    """Merge, not replace. PUT on the collection sets the keys it names and
    leaves the rest — a client sending one field should not silently erase a
    preference it never knew about."""
    for key, value in values.items():
        set_preference(user_id, key, value)
    return get_preferences(user_id)
