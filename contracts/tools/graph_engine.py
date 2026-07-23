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
    # Set when the currency or the target program is not a node in the transfer
    # graph at all (spec update 2026-07-20, closes KNOWN_LIMITATIONS item 17).
    #
    # Empty `paths` used to mean two different things: "this currency is known
    # and has no verified route to the target" and "we hold no transfer data for
    # this currency whatsoever". The first is an answer; the second is missing
    # data, and reporting it as an answer is how an unregistered issuer looked
    # like a card with no transfer options.
    no_transfer_data: str | None = None

    @property
    def is_unresolved_input(self) -> bool:
        """True when the currency or the target program is not in the graph, so
        the tool could not resolve its input and produced no paths. Lifted to a
        distinct `unresolved_input` status by the Tool Registry, so "I couldn't
        identify that program" never has to be inferred from empty `paths`
        (KNOWN_LIMITATIONS 24, Class B)."""
        return self.no_transfer_data is not None and not self.paths


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
    # One entry per portfolio currency the transfer graph does not know about
    # (spec update 2026-07-20). Without this, a portfolio of entirely
    # unregistered cards returns zero options and reads as "nothing to
    # recommend" rather than "we have no data on your cards".
    no_transfer_data: list[str] = Field(default_factory=list)

    @property
    def is_unresolved_input(self) -> bool:
        """True only when there are *no* options AND the reason is unresolved
        input (an unregistered target program, or every held currency absent
        from the graph). A partial result — some currencies resolved, some not —
        is a real answer with caveats, so it stays `success` with the
        `no_transfer_data` entries riding along (KNOWN_LIMITATIONS 24, Class B)."""
        return bool(self.no_transfer_data) and not self.options
