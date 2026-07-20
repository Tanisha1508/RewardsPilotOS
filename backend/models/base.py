"""Declarative base and shared column types (BUILD_SPEC §4).

The models mirror the spec'd schema exactly — same tables, same columns, same
names. Adding a column here is a schema change and therefore a spec decision,
not an implementation detail (Build Constraints, BUILD_SPEC §2).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def pk_uuid():
    """Server-independent UUID primary key, generated in Python so a row's id
    is known before flush (the API returns it in the create response)."""
    return mapped_column(primary_key=True, default=uuid.uuid4)


def created_at_column():
    return mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


def updated_at_column():
    return mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
