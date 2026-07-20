"""Where memory tools get their data.

Same seam and same reasoning as `tools/portfolio/source.py`: the handler
signatures are spec'd, so the source is resolved rather than injected, and
Postgres is the default with no fixture fallback.

The Postgres source is deliberately thin — the queries live in `memory/`, which
is the subsystem that owns them (semantic memory in `memory/semantic/`,
episodic in `memory/episodic/`). This module only adapts them to the tool
contracts.
"""

import uuid
from typing import Protocol

from contracts.tools.memory import EpisodicEvent
from memory.episodic.store import recent_events, record_event
from memory.semantic.store import get_preferences, set_preference


class UnknownUserError(Exception):
    pass


class MemorySource(Protocol):
    def preferences(self, user_id: str) -> dict[str, str]: ...

    def episodic(self, user_id: str, limit: int) -> list[EpisodicEvent]: ...

    def store_preference(self, user_id: str, key: str, value: str) -> None: ...


def _uuid(user_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(user_id)
    except ValueError as exc:
        raise UnknownUserError(f"not a valid user id: {user_id!r}") from exc


class PostgresMemorySource:
    def preferences(self, user_id: str) -> dict[str, str]:
        return get_preferences(_uuid(user_id))

    def episodic(self, user_id: str, limit: int) -> list[EpisodicEvent]:
        return [
            EpisodicEvent(
                event_id=event.event_id,
                event_type=event.event_type,
                payload=event.payload,
                created_at=event.created_at.isoformat(),
            )
            for event in recent_events(_uuid(user_id), limit)
        ]

    def store_preference(self, user_id: str, key: str, value: str) -> None:
        set_preference(_uuid(user_id), key, value)

    def record(self, user_id: str, event_type: str, payload: dict) -> None:
        record_event(_uuid(user_id), event_type, payload)


class InMemoryMemorySource:
    """Seeded fake for tests and the evaluation harness. Never the default."""

    def __init__(self, seed: dict) -> None:
        self._preferences = {seed["user_id"]: dict(seed["preferences"])}
        self._episodic = {seed["user_id"]: [EpisodicEvent(**event) for event in seed["episodic"]]}

    def preferences(self, user_id: str) -> dict[str, str]:
        return dict(self._preferences.get(user_id, {}))

    def episodic(self, user_id: str, limit: int) -> list[EpisodicEvent]:
        events = self._episodic.get(user_id, [])
        return sorted(events, key=lambda e: e.created_at, reverse=True)[:limit]

    def store_preference(self, user_id: str, key: str, value: str) -> None:
        self._preferences.setdefault(user_id, {})[key] = value


_source: MemorySource | None = None


def get_source() -> MemorySource:
    global _source
    if _source is None:
        _source = PostgresMemorySource()
    return _source


def set_source(source: MemorySource | None) -> None:
    global _source
    _source = source
