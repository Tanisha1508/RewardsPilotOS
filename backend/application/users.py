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


def delete_user(user_id: uuid.UUID) -> None:
    """Erase everything this service holds about a user (privacy audit P3).

    One `delete` on the `users` row. Every table that references a user does so
    with `ON DELETE CASCADE`, so portfolios, cards, balances, loyalty accounts,
    preferences, goals, recommendations, interaction events and notifications go
    with it. Deleting them individually here would be a second list to keep in
    step with the schema, and the first thing to fall out of date when a table
    is added.

    Idempotent: deleting an already-absent user is success, not 404. The caller
    asked for the data to be gone and it is gone — and a user who deletes their
    account, then retries because the response was slow, should not receive an
    error.

    **This does not delete the Supabase auth identity.** That lives in
    `auth.users`, reachable only with the service-role key, which this service
    deliberately does not hold. So the person can sign in again and get a fresh,
    empty account. The UI says so rather than implying a clean wipe.
    """
    with session_scope() as session:
        user = session.get(User, user_id)
        if user is not None:
            session.delete(user)


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
