"""Preferences endpoints, delegating to semantic memory.

Deliberately thin. The preference store lives in `memory/semantic/` because
preferences *are* the semantic memory layer (MASTER_SPEC ch. 22); duplicating
the queries here would give the UI and the agent two code paths to the same
rows, which is how they drift.
"""

import uuid

from backend.application.errors import NotFoundError
from memory.semantic.store import delete_preference, get_preferences, set_preference


def read_preferences(user_id: uuid.UUID) -> dict[str, str]:
    return get_preferences(user_id)


def write_preferences(user_id: uuid.UUID, values: dict[str, str]) -> dict[str, str]:
    """Merge, not replace. PUT on the collection sets the keys it names and
    leaves the rest — a client sending one field should not silently erase a
    preference it never knew about."""
    for key, value in values.items():
        set_preference(user_id, key, value)
    return get_preferences(user_id)


def remove_preference(user_id: uuid.UUID, key: str) -> None:
    """Delete one preference outright.

    `write_preferences` merges by design, so it can set a key but never unset
    one — a user could change a preference and never remove it. Clearing the
    value was the only workaround, and an empty string is still a stored
    preference the agent reads, not an absence.

    404 on an unknown key rather than silent success: "it is gone" and "it was
    never there" are different answers, and a UI that cannot tell them apart
    will happily show a delete button for a key that does not exist.
    """
    if not delete_preference(user_id, key):
        raise NotFoundError(f"no preference named {key!r}")
