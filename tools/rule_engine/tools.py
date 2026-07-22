"""Rule Engine tools: CalculateEarn, CheckCap, CompareCards."""

from pydantic import BaseModel

from contracts.tools.rule_engine import (
    CalculateEarnInput,
    CapStatus,
    CheckCapInput,
    CompareCardsInput,
    EarnResult,
)
from rules.engine.engine import RuleEngine
from rules.evaluator.validity import current_month

_engine = RuleEngine()


class CompareCardsOutput(BaseModel):
    results: list[EarnResult]


def _month(supplied: str | None) -> str:
    """Resolve an absent month to the current one.

    This is the single boundary where "now" enters the Rule Engine. The engine
    itself takes a required month and has no default — since ADR-012 the month
    selects which accelerated programs are in force, so a silently-defaulted
    month is not inert: it can turn a live rate off, or a lapsed one back on.
    Resolving here keeps that decision in one readable place, and keeps the
    engine a pure function of its arguments.
    """
    return supplied or current_month()


def calculate_earn(args: CalculateEarnInput) -> EarnResult:
    return _engine.calculate_earn(
        args.card_key, args.amount, args.category, args.channel, _month(args.month)
    )


def check_cap(args: CheckCapInput) -> CapStatus:
    return _engine.check_cap(args.card_key, args.cap_scope, _month(args.month))


def compare_cards(args: CompareCardsInput) -> CompareCardsOutput:
    return CompareCardsOutput(
        results=_engine.compare_cards(
            args.cards, args.amount, args.category, args.channel, _month(args.month)
        )
    )
