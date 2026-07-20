"""Portfolio tools (BUILD_SPEC §8).

Signatures are unchanged from the sprint; only where the data comes from has
moved. See `tools/portfolio/source.py` for why the source is resolved rather
than passed in.
"""

from contracts.tools.portfolio import (
    GetCardsOutput,
    GetPortfolioOutput,
    GetRewardBalancesOutput,
    GetTravelGoalsOutput,
    UserScopedInput,
)
from tools.portfolio.source import get_source


def get_portfolio(args: UserScopedInput) -> GetPortfolioOutput:
    return get_source().portfolio(args.user_id)


def get_cards(args: UserScopedInput) -> GetCardsOutput:
    return get_source().cards(args.user_id)


def get_reward_balances(args: UserScopedInput) -> GetRewardBalancesOutput:
    return get_source().balances(args.user_id)


def get_travel_goals(args: UserScopedInput) -> GetTravelGoalsOutput:
    return get_source().goals(args.user_id)
