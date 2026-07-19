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


class Fees(BaseModel):
    """Card fee facts (spec update 2026-07-19). annual_fee and the renewal
    waiver are distinct facts — never conflated. A waiver field left as None
    means 'confirmed not applicable' (finding recorded in notes), which is
    different from an unverified value."""

    annual_fee_inr: VerifiedValue
    renewal_fee_waiver_spend_inr: VerifiedValue | None = None
    forex_markup_pct: VerifiedValue | None = None
    notes: str | None = None


class ContinuationEligibility(BaseModel):
    """Card retention requirement (spec update 2026-07-19): annual spend OR
    relationship value, whichever is met (any_of)."""

    annual_spend_inr: VerifiedValue
    relationship_value_inr: VerifiedValue
    requirement: str = "any_of"
    effective_from: str | None = None
    notes: str | None = None


class WelcomeBonusCohort(BaseModel):
    """Welcome bonus terms vary by issuance cohort (spec update 2026-07-19,
    Axis Atlas verification): one entry per issuance window."""

    issued_from: str | None = None  # ISO date; None = beginning of program
    issued_to: str | None = None  # ISO date; None = open-ended
    bonus_points: VerifiedValue
    qualifying_transactions: int = 1
    qualifying_spend_inr: VerifiedValue | None = None  # spend-based qualification
    window_days: int | None = None
    notes: str | None = None


class TierBenefit(BaseModel):
    """Spend-tier structure (spec update 2026-07-19, Axis Atlas
    verification): tier entry threshold and annual renewal bonus."""

    name: str
    annual_spend_threshold_inr: VerifiedValue
    renewal_bonus_points: VerifiedValue
    notes: str | None = None


class CatalogueRedemption(BaseModel):
    """Card-specific catalogue redemption tier (spec update 2026-07-20, Amex
    Platinum Travel): per-brand rate when no single voucher-channel value
    exists."""

    brand: str
    rate_per_point_inr: VerifiedValue
    notes: str | None = None


class PointsExpiry(BaseModel):
    """Points expiry policy (spec update 2026-07-20): some programs never
    expire points rather than using a duration."""

    never_expires: bool
    forfeit_on_cancellation_days: int | None = None
    effective_from: str | None = None
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
    fees: Fees | None = None
    continuation_eligibility: ContinuationEligibility | None = None
    welcome_bonus: list[WelcomeBonusCohort] = Field(default_factory=list)
    tiers: list[TierBenefit] = Field(default_factory=list)
    redemption_catalogue: list[CatalogueRedemption] = Field(default_factory=list)
    points_expiry: PointsExpiry | None = None
