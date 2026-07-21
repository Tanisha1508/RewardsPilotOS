"""Recommendation history and feedback (BUILD_SPEC §9).

Reads and status transitions over the `recommendations` table. A stored
recommendation is a record of what the user was told, so it is never
regenerated or re-rendered from current data — only its `status` changes as the
user views, accepts, rejects, or saves it.
"""

import uuid

from sqlalchemy import select

from backend.application.errors import NotFoundError, PermissionDeniedError
from backend.models.intelligence import InteractionEvent, Recommendation
from database.postgres.session import session_scope

# Terminal feedback states the user sets; "viewed" is set implicitly on GET.
FEEDBACK_STATUSES = ("accepted", "rejected", "saved")


def _owned(session, user_id: uuid.UUID, rec_id: uuid.UUID) -> Recommendation:
    row = session.get(Recommendation, rec_id)
    if row is None:
        raise NotFoundError(f"recommendation {rec_id} not found")
    if row.user_id != user_id:
        # Reported as 404, never 403 — do not confirm another user's row exists.
        raise PermissionDeniedError(f"recommendation {rec_id} not found")
    return row


def list_recommendations(user_id: uuid.UUID, limit: int = 20) -> list[Recommendation]:
    with session_scope() as session:
        rows = list(
            session.scalars(
                select(Recommendation)
                .where(Recommendation.user_id == user_id)
                .order_by(Recommendation.created_at.desc())
                .limit(limit)
            )
        )
        for row in rows:
            session.expunge(row)
        return rows


def get_recommendation(user_id: uuid.UUID, rec_id: uuid.UUID) -> Recommendation:
    """Fetch one, marking it viewed. 'viewed' never overwrites a terminal
    feedback state (accepted/rejected/saved) the user already set."""
    with session_scope() as session:
        row = _owned(session, user_id, rec_id)
        if row.status == "generated":
            row.status = "viewed"
        session.flush()
        session.expunge(row)
        return row


def record_feedback(user_id: uuid.UUID, rec_id: uuid.UUID, status: str) -> Recommendation:
    with session_scope() as session:
        row = _owned(session, user_id, rec_id)
        row.status = status
        # Feedback is episodic memory too — what the user did with the answer
        # (BUILD_SPEC §4, interaction_events; feeds the memory loop).
        session.add(
            InteractionEvent(
                user_id=user_id,
                event_type=f"recommendation_{status}",
                payload_json={"rec_id": str(rec_id)},
            )
        )
        session.flush()
        session.expunge(row)
        return row
