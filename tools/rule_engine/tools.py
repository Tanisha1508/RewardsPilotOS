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

_engine = RuleEngine()


class CompareCardsOutput(BaseModel):
    results: list[EarnResult]


def calculate_earn(args: CalculateEarnInput) -> EarnResult:
    return _engine.calculate_earn(
        args.card_key, args.amount, args.category, args.channel, args.month
    )


def check_cap(args: CheckCapInput) -> CapStatus:
    return _engine.check_cap(args.card_key, args.cap_scope, args.month)


def compare_cards(args: CompareCardsInput) -> CompareCardsOutput:
    return CompareCardsOutput(
        results=_engine.compare_cards(
            args.cards, args.amount, args.category, args.channel, args.month
        )
    )
