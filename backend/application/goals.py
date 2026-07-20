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
