"""Portfolio tools (BUILD_SPEC §8).

Handler signatures are unchanged from the sprint; what has moved is where the
data comes from (`tools/portfolio/source.py`) and, since 2026-07-22, where the
*caller's identity* comes from. These tools load the caller's own data, so the
user is resolved from the ambient `acting_as` context rather than taken as an
argument — the same pattern `tools/graph_engine/tools.py` has always used.
Identity is never read from model output (KNOWN_LIMITATIONS 24, Class C).
"""

from contracts.tools.portfolio import (
    GetCardsOutput,
    GetPortfolioOutput,
    GetRewardBalancesOutput,
    GetTravelGoalsOutput,
    UserScopedInput,
)
from tools.portfolio.source import current_user, get_source


def get_portfolio(args: UserScopedInput) -> GetPortfolioOutput:
    return get_source().portfolio(current_user())


def get_cards(args: UserScopedInput) -> GetCardsOutput:
    return get_source().cards(current_user())


def get_reward_balances(args: UserScopedInput) -> GetRewardBalancesOutput:
    return get_source().balances(current_user())


def get_travel_goals(args: UserScopedInput) -> GetTravelGoalsOutput:
    return get_source().goals(current_user())
