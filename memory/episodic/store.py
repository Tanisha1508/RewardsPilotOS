"""Episodic memory: what the user did, in order (MASTER_SPEC ch. 22).

Backed by `interaction_events`, which BUILD_SPEC §4 also designates as the
analytics instrumentation table — the same rows serve both, so an event
recorded for analysis is recallable by the agent without a second write path.

Events are append-only. Recall is most-recent-first and always limited: the
point is relevant recent context, and an unbounded history would push the
useful part of a prompt out of the window.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select

from backend.models.intelligence import InteractionEvent
from database.postgres.session import session_scope


@dataclass(frozen=True)
class Event:
    """Detached read model, so callers never hold a live ORM object across a
    closed session."""

    event_id: str
    event_type: str
    payload: dict
    created_at: datetime


def record_event(user_id: uuid.UUID, event_type: str, payload: dict | None = None) -> Event:
    with session_scope() as session:
        row = InteractionEvent(user_id=user_id, event_type=event_type, payload_json=payload or {})
        session.add(row)
        session.flush()
        return _to_event(row)


def recent_events(user_id: uuid.UUID, limit: int = 5) -> list[Event]:
    with session_scope() as session:
        rows = session.scalars(
            select(InteractionEvent)
            .where(InteractionEvent.user_id == user_id)
            .order_by(InteractionEvent.created_at.desc(), InteractionEvent.event_id.desc())
            .limit(limit)
        )
        return [_to_event(row) for row in rows]


def _to_event(row: InteractionEvent) -> Event:
    return Event(
        event_id=str(row.event_id),
        event_type=row.event_type,
        payload=dict(row.payload_json or {}),
        created_at=row.created_at,
    )
