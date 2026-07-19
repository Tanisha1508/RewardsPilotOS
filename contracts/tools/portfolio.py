"""Portfolio tool contracts: GetPortfolio, GetCards, GetRewardBalances,
GetTravelGoals (BUILD_SPEC §8, MASTER_SPEC ch. 21). Sprint returns fixture
data; D2 wires Postgres behind the same schemas."""

from pydantic import BaseModel, Field


class UserScopedInput(BaseModel):
    user_id: str


class Card(BaseModel):
    card_id: str
    issuer: str
    card_name: str
    network: str
    reward_currency: str
    status: str = "active"
    annual_fee: float | None = None
    renewal_date: str | None = None


class GetPortfolioOutput(BaseModel):
    portfolio_id: str
    portfolio_name: str
    user_id: str
    cards: list[Card] = Field(default_factory=list)


class GetCardsOutput(BaseModel):
    cards: list[Card] = Field(default_factory=list)


class RewardBalance(BaseModel):
    card_id: str
    reward_currency: str
    current_balance: float
    expiry_date: str | None = None
    last_updated: str


class GetRewardBalancesOutput(BaseModel):
    balances: list[RewardBalance] = Field(default_factory=list)


class TravelGoal(BaseModel):
    goal_id: str
    goal_type: str  # trip | redemption | savings
    description: str
    target_date: str | None = None
    status: str = "active"
    target_program: str | None = None
    required_points: float | None = None


class GetTravelGoalsOutput(BaseModel):
    goals: list[TravelGoal] = Field(default_factory=list)
