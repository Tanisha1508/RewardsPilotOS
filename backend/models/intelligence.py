"""Recommendation, event, and notification tables (BUILD_SPEC §4).

`interaction_events` is the episodic memory layer (MASTER_SPEC ch. 22) as well
as analytics instrumentation — the same rows `RecallMemory` reads back.

`recommendations` stores `recommendation_json` and `citations_json` as written.
A stored recommendation is a record of what the user was actually told, so it
is never regenerated or re-rendered from current data: the numbers and
citations must stay as they were at the time, even after the rules change.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, created_at_column, pk_uuid


class Recommendation(Base):
    __tablename__ = "recommendations"

    rec_id: Mapped[uuid.UUID] = pk_uuid()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(String, nullable=False)
    recommendation_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[str | None] = mapped_column(String(10))  # high|medium|low
    citations_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # generated|viewed|accepted|rejected|saved
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="generated")
    created_at: Mapped[datetime] = created_at_column()


class InteractionEvent(Base):
    __tablename__ = "interaction_events"

    event_id: Mapped[uuid.UUID] = pk_uuid()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = created_at_column()


class Notification(Base):
    __tablename__ = "notifications"

    notif_id: Mapped[uuid.UUID] = pk_uuid()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str | None] = mapped_column(String)
    source_change_id: Mapped[str | None] = mapped_column(String(200))
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = created_at_column()
