"""User, preference, and goal tables (BUILD_SPEC §4).

`users.user_id` mirrors the Supabase `auth.users` id rather than generating its
own: the JWT `sub` claim is the identity, and a locally-minted id would be a
second source of truth for who someone is.

`preferences` is the semantic memory layer (MASTER_SPEC ch. 22) — the same rows
`RecallMemory` reads and `StorePreference` writes.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, created_at_column, pk_uuid, updated_at_column


class User(Base):
    __tablename__ = "users"

    # Not defaulted: the id comes from Supabase, never from us.
    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    name: Mapped[str | None] = mapped_column(String(200))
    timezone: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()


class Preference(Base):
    __tablename__ = "preferences"
    # One value per key per user: storing a second row would make "the user's
    # home airport" ambiguous, and the reader has no way to pick.
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_preferences_user_key"),)

    pref_id: Mapped[uuid.UUID] = pk_uuid()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = updated_at_column()


class Goal(Base):
    __tablename__ = "goals"

    goal_id: Mapped[uuid.UUID] = pk_uuid()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    goal_type: Mapped[str] = mapped_column(String(20), nullable=False)  # trip|redemption|savings
    description: Mapped[str] = mapped_column(String, nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
