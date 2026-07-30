"""HTTP DTOs for auth, preferences, and goals."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class SyncIn(BaseModel):
    """Optional profile fields. Identity itself is never taken from the body —
    `user_id` comes from the verified token's `sub`, so a client cannot sync
    someone else's row by naming them here."""

    name: str | None = Field(default=None, max_length=200)
    timezone: str | None = Field(default=None, max_length=64)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: str
    name: str | None = None
    timezone: str | None = None


class PreferencesIn(BaseModel):
    values: dict[str, str]


class PreferencesOut(BaseModel):
    values: dict[str, str]


class GoalIn(BaseModel):
    goal_type: str = Field(pattern="^(trip|redemption|savings)$")
    description: str = Field(min_length=1)
    target_date: date | None = None
    status: str = "active"


class GoalPatch(BaseModel):
    """PATCH body: every field optional, and an omitted field means "leave it".

    Separate from `GoalIn` rather than `GoalIn` with defaults, because the two
    say different things. `GoalIn` requires a description — a goal without one
    is meaningless. `GoalPatch` must allow a caller to send only `status`
    without restating the description, and `exclude_unset` at the route keeps
    "not sent" distinct from "explicitly null" — which is the difference
    between leaving a deadline alone and removing it.
    """

    goal_type: str | None = Field(default=None, pattern="^(trip|redemption|savings)$")
    description: str | None = Field(default=None, min_length=1)
    target_date: date | None = None
    status: str | None = None


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    goal_id: uuid.UUID
    goal_type: str
    description: str
    target_date: date | None = None
    status: str
