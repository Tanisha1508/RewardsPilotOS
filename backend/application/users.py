"""User sync and lookup (BUILD_SPEC §9: `POST /api/v1/auth/sync`).

Supabase owns identity; this table mirrors it. `sync_user` is therefore an
upsert keyed on the token's `sub`, not an insert: it is called after every
signup *and* every login, and the second call must be a no-op rather than a
duplicate-key error.

A user gets a default portfolio on first sync. Every card hangs off a
portfolio (BUILD_SPEC §4), so a user without one cannot add a card, and making
the client create it first would let a signup half-finish.
"""

import uuid

from sqlalchemy import select

from backend.models.identity import User
from backend.models.portfolio import Portfolio
from database.postgres.session import session_scope

DEFAULT_PORTFOLIO_NAME = "My cards"


def sync_user(user_id: uuid.UUID, email: str | None, name: str | None = None) -> User:
    with session_scope() as session:
        user = session.get(User, user_id)
        if user is None:
            user = User(user_id=user_id, email=email or f"{user_id}@unknown.invalid", name=name)
            session.add(user)
            session.flush()
            session.add(Portfolio(user_id=user_id, portfolio_name=DEFAULT_PORTFOLIO_NAME))
        else:
            # Supabase is the source of truth for email; a changed address there
            # should not leave a stale copy here.
            if email:
                user.email = email
            if name:
                user.name = name
        session.flush()
        return user


def get_user(user_id: uuid.UUID) -> User | None:
    with session_scope() as session:
        return session.get(User, user_id)


def default_portfolio(user_id: uuid.UUID) -> Portfolio | None:
    with session_scope() as session:
        return session.scalars(
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .order_by(Portfolio.created_at)
            .limit(1)
        ).first()
