"""Rule Engine tool contracts: inputs and outputs for CalculateEarn, CheckCap,
CompareCards (BUILD_SPEC §5, §8).

These models are the cross-boundary interface between the Rule Engine domain
and the Tool Registry / agents. All numbers in `EarnResult` are deterministic
engine outputs; the LLM copies them verbatim and never alters them.
"""

from typing import Literal

from pydantic import BaseModel, Field

from contracts.api.verified_value import VerifiedValue


class CalculateEarnInput(BaseModel):
    card_key: str
    amount: float = Field(gt=0)
    category: str
    channel: str | None = None
    month: str = Field(pattern=r"^\d{4}-\d{2}$")


class CheckCapInput(BaseModel):
    card_key: str
    cap_scope: str
    month: str = Field(pattern=r"^\d{4}-\d{2}$")


class CompareCardsInput(BaseModel):
    cards: list[str] = Field(min_length=1)
    amount: float = Field(gt=0)
    category: str
    channel: str | None = None
    month: str = Field(pattern=r"^\d{4}-\d{2}$")


class EarnResult(BaseModel):
    card_key: str
    amount: float
    category: str
    channel: str | None
    month: str
    status: Literal["computed", "unknown", "excluded"]
    points: float | None = None
    applied: Literal["base", "accelerated"] | None = None
    rate: VerifiedValue = Field(default_factory=VerifiedValue.unknown)
    multiplier: VerifiedValue | None = None
    points_before_cap: float | None = None
    cap_applied: bool = False
    cap_scope: str | None = None
    unknown_reasons: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    rule_version: int | None = None


class CapStatus(BaseModel):
    card_key: str
    scope: str
    period: str
    month: str
    cap_points: VerifiedValue = Field(default_factory=VerifiedValue.unknown)
    accrued_points: float = 0.0
    remaining_points: float | None = None
    status: Literal["ok", "reached", "unknown"]
    unknown_reasons: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
