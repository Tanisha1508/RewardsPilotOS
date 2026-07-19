"""Portfolio tools (fixture-backed for the sprint)."""

from contracts.tools.portfolio import (
    GetCardsOutput,
    GetPortfolioOutput,
    GetRewardBalancesOutput,
    GetTravelGoalsOutput,
    UserScopedInput,
)
from tools.portfolio.fixtures import BALANCES, CARDS, GOALS


def get_portfolio(args: UserScopedInput) -> GetPortfolioOutput:
    return GetPortfolioOutput(
        portfolio_id="portfolio_fixture_1",
        portfolio_name="Primary portfolio (fixture)",
        user_id=args.user_id,
        cards=CARDS,
    )


def get_cards(args: UserScopedInput) -> GetCardsOutput:
    return GetCardsOutput(cards=CARDS)


def get_reward_balances(args: UserScopedInput) -> GetRewardBalancesOutput:
    return GetRewardBalancesOutput(balances=BALANCES)


def get_travel_goals(args: UserScopedInput) -> GetTravelGoalsOutput:
    return GetTravelGoalsOutput(goals=GOALS)
