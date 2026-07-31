"""Rule Engine tool contracts: inputs and outputs for CalculateEarn, CheckCap,
CompareCards (BUILD_SPEC §5, §8).

These models are the cross-boundary interface between the Rule Engine domain
and the Tool Registry / agents. All numbers in `EarnResult` are deterministic
engine outputs; the LLM copies them verbatim and never alters them.
"""

from typing import Literal

from pydantic import BaseModel, Field

from contracts.api.verified_value import VerifiedValue

# Absent means "the current month", resolved at the tool boundary
# (`tools/rule_engine/tools.py`) — never defaulted here, and never defaulted in
# an engine signature. Most real queries carry no period ("which card for a
# ₹50,000 flight?"), so a *required* month is an argument the Planner can only
# invent; it correctly declines, the invocation is rejected by validation, and
# the computation is silently lost (KNOWN_LIMITATIONS 24, found by the first
# live smoke run). The pattern still applies whenever a month IS supplied, so a
# malformed value is rejected exactly as before — absent and malformed are
# different states and stay that way.
_MONTH = Field(default=None, pattern=r"^\d{4}-\d{2}$")


class CalculateEarnInput(BaseModel):
    card_key: str
    amount: float = Field(gt=0)
    category: str
    channel: str | None = None
    month: str | None = _MONTH


class CheckCapInput(BaseModel):
    card_key: str
    cap_scope: str
    month: str | None = _MONTH


class CompareCardsInput(BaseModel):
    cards: list[str] = Field(min_length=1)
    amount: float = Field(gt=0)
    category: str
    channel: str | None = None
    month: str | None = _MONTH


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
    # Set when an accelerated entry matched the query but fell outside its
    # validity window, so `points` is base earn rather than accelerated
    # (ADR-012). Deterministic text; the Recommender may repeat it verbatim.
    expiry_note: str | None = None
    # Set when NO channel was supplied and the card has an in-force accelerated
    # entry for this category, so `points` is base earn only because the booking
    # channel is unknown — not because the card earns base here.
    #
    # Without this, a channel-less query silently scored every card at base and
    # reported a winner at high confidence, even though naming the channel could
    # change which card wins (found live 2026-07-28: a Rs 50,000 flight ranked
    # hdfc_infinia 1665 > axis_atlas 1000, where axis_atlas earns 2500 booking
    # direct). Deterministic text; the Recommender repeats it verbatim.
    channel_note: str | None = None
    # Set when the queried category is not a word any rule file uses AND this
    # card has bonus categories that were therefore not matched (B2,
    # KNOWN_LIMITATIONS 30). An unmapped category earns base silently, which is
    # correct for genuinely different spend and wrong for an unrecognised
    # synonym — `hotel` for `hotels` cost a 10x under-report that way. The two
    # are indistinguishable to the engine, so it reports what it did and what
    # else the card offers rather than guessing. Deterministic text; the
    # Recommender repeats it verbatim.
    category_note: str | None = None
    # What the rate is actually per, and in what currency (A4, 2026-07-31).
    #
    # Without these the UI could only print a bare "Rate 2" beside a bare
    # "Rate 5" — and those are 2 EDGE Miles per INR 100 against 5 HDFC points
    # per INR 150. Shown side by side they read as "Infinia is 2.5x better",
    # which is false twice over: different denominators and different
    # currencies. The engine knew both and kept them to itself.
    #
    # Carried rather than computed downstream: turning them into a per-rupee
    # figure would be arithmetic outside the engine, and comparing two
    # currencies needs a valuation this product refuses to assume.
    rate_per_amount: float | None = None
    reward_currency: str | None = None
    unknown_reasons: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    rule_version: int | None = None


class CapStatus(BaseModel):
    card_key: str
    scope: str
    period: str
    month: str
    cap_points: VerifiedValue = Field(default_factory=VerifiedValue.unknown)
    # None means the system has never tracked this cardholder's spend for the
    # scope — the normal case, since nothing records accrual. Distinct from 0.0,
    # which means tracked and nothing accrued. Defaulting this to 0.0 is what
    # let CheckCap answer "you have used 0 of 15,000" from an empty table.
    accrued_points: float | None = None
    remaining_points: float | None = None
    status: Literal["ok", "reached", "unknown"]
    unknown_reasons: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
