"""Goals (BUILD_SPEC §9: `GET/POST /api/v1/goals`).

Goals are what redemption planning aims at — the Graph Engine's
`RedemptionOptions` reads them through the `GetTravelGoals` tool. They are
user-stated, never inferred from behaviour.
"""

import uuid
from datetime import date

from sqlalchemy import select

from backend.application.errors import NotFoundError
from backend.models.identity import Goal, User
from database.postgres.session import session_scope

GOAL_TYPES = ("trip", "redemption", "savings")


def list_goals(user_id: uuid.UUID) -> list[Goal]:
    with session_scope() as session:
        return list(
            session.scalars(select(Goal).where(Goal.user_id == user_id).order_by(Goal.target_date))
        )


def create_goal(
    user_id: uuid.UUID,
    goal_type: str,
    description: str,
    target_date: date | None = None,
    status: str = "active",
) -> Goal:
    with session_scope() as session:
        if session.get(User, user_id) is None:
            raise NotFoundError("unknown user — call POST /api/v1/auth/sync first")
        goal = Goal(
            user_id=user_id,
            goal_type=goal_type,
            description=description,
            target_date=target_date,
            status=status,
        )
        session.add(goal)
        session.flush()
        return goal


def _owned_goal(session, user_id: uuid.UUID, goal_id: uuid.UUID) -> Goal:
    """A goal, only if it belongs to this user.

    Scoped by owner in the lookup itself rather than fetched-then-checked: the
    two are equivalent here, but the first cannot be got wrong by a later edit
    that forgets the check. A goal belonging to someone else is `NotFoundError`,
    not a permission error — telling a caller that an id exists but is not
    theirs confirms the id.
    """
    goal = session.scalars(
        select(Goal).where(Goal.goal_id == goal_id, Goal.user_id == user_id)
    ).first()
    if goal is None:
        raise NotFoundError("goal not found")
    return goal


def update_goal(user_id: uuid.UUID, goal_id: uuid.UUID, **changes) -> Goal:
    """PATCH semantics: an omitted field means "leave it alone".

    `target_date` is the one field where an explicit null is meaningful —
    removing a deadline is a real edit — so callers pass it explicitly and
    unset fields never reach here.
    """
    with session_scope() as session:
        goal = _owned_goal(session, user_id, goal_id)
        for field, value in changes.items():
            setattr(goal, field, value)
        session.flush()
        return goal


def delete_goal(user_id: uuid.UUID, goal_id: uuid.UUID) -> None:
    with session_scope() as session:
        session.delete(_owned_goal(session, user_id, goal_id))
