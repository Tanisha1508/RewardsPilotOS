"""Pydantic models for versioned rule JSON files (BUILD_SPEC §5)."""

from pydantic import BaseModel, Field

from contracts.api.verified_value import VerifiedValue


class BaseEarn(BaseModel):
    rate: VerifiedValue
    per_amount: float = Field(gt=0)
    currency: str


class AcceleratedEarn(BaseModel):
    channel: str
    category: str
    multiplier: VerifiedValue
    monthly_cap_points: VerifiedValue = Field(default_factory=VerifiedValue.unknown)
    cap_scope: str | None = None
    notes: str | None = None


class Cap(BaseModel):
    scope: str
    period: str
    cap_points: VerifiedValue


class Milestone(BaseModel):
    spend_threshold: VerifiedValue
    bonus_points: VerifiedValue
    period: str
    notes: str | None = None


class RuleFile(BaseModel):
    card_key: str
    version: int
    effective_date: str
    reward_currency: str
    base_earn: BaseEarn
    accelerated: list[AcceleratedEarn] = Field(default_factory=list)
    caps: list[Cap] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    milestones: list[Milestone] = Field(default_factory=list)
    point_value_reference_inr: VerifiedValue = Field(default_factory=VerifiedValue.unknown)
