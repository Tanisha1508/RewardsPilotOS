"""Pydantic models for versioned rule JSON files (BUILD_SPEC §5)."""

from pydantic import BaseModel, Field

from contracts.api.verified_value import PointValueReference, VerifiedValue


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
    effective_date: str | None = None
    notes: str | None = None


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
    # Per-channel since the 2026-07-19 spec update: a point's INR value
    # depends on the redemption channel (cashback / voucher / travel).
    point_value_reference_inr: PointValueReference = Field(
        default_factory=PointValueReference.unknown
    )
