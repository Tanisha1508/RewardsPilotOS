"""Graph Engine tool contracts: BestTransferPaths and RedemptionOptions
(BUILD_SPEC §7, §8).

All ratios come from verified edges. Null/unverified edges never enter path
math — they are surfaced only as "unverified path exists"."""

from typing import Literal

from pydantic import BaseModel, Field

from contracts.api.verified_value import VerifiedValue


class BestTransferPathsInput(BaseModel):
    currency: str
    target_program: str
    max_hops: int = Field(default=3, ge=1, le=5)


class TransferPath(BaseModel):
    nodes: list[str]
    cumulative_ratio: float
    min_transfer: float | None = None
    sources: list[str] = Field(default_factory=list)
    last_verified: str | None = None  # oldest verification date along the path


class BestTransferPathsOutput(BaseModel):
    currency: str
    target_program: str
    paths: list[TransferPath] = Field(default_factory=list)
    unverified_paths_exist: bool = False
    unverified_notes: list[str] = Field(default_factory=list)


class RedemptionGoal(BaseModel):
    target_program: str
    required_points: float | None = Field(default=None, gt=0)
    description: str | None = None
    # Which per-channel point value applies (spec update 2026-07-19).
    # Transfer-to-program redemptions are travel redemptions by default.
    redemption_type: Literal["cashback", "voucher", "travel"] = "travel"


class RedemptionOptionsInput(BaseModel):
    # reward currency -> current balance; when omitted the tool loads the
    # user's current balances itself (deterministic data access)
    portfolio: dict[str, float] | None = None
    goal: RedemptionGoal


class RedemptionOption(BaseModel):
    currency: str
    target_program: str
    path: TransferPath
    points_required: float | None = None
    balance: float
    balance_sufficient: bool | None = None
    # The point value for the goal's redemption channel, selected from the
    # per-channel reference table (spec update 2026-07-19).
    value_channel: str = "travel"
    point_value_reference_inr: VerifiedValue = Field(default_factory=VerifiedValue.unknown)
    value_estimate_inr: float | None = None
    value_status: str = "unknown"  # "computed" only when point value is verified
    notes: list[str] = Field(default_factory=list)


class RedemptionOptionsOutput(BaseModel):
    target_program: str
    options: list[RedemptionOption] = Field(default_factory=list)
    unverified_paths_exist: bool = False
    unverified_notes: list[str] = Field(default_factory=list)
