"""Portfolio tool contracts: GetPortfolio, GetCards, GetRewardBalances,
GetTravelGoals (BUILD_SPEC §8, MASTER_SPEC ch. 21). Sprint returns fixture
data; D2 wires Postgres behind the same schemas."""

from pydantic import BaseModel, Field


class UserScopedInput(BaseModel):
    """Input for tools that load *the caller's own* data. Deliberately empty.

    `user_id` was a required field here until 2026-07-22, which meant the
    identity these tools read was whatever the LLM put in the plan. The
    authenticated value was already in context — `backend/application/chat.py`
    wraps every run in `acting_as(user_id)` from the verified JWT — so the model
    was relaying a value the runtime already knew, and the tools trusted the
    relay over the source. `tools/graph_engine/tools.py` had always resolved it
    correctly via `current_user()`; the other seven tools had not.

    The field is *removed* rather than ignored-if-present, for the same reason
    the engine's `month="1970-01"` default was deleted rather than left as a
    bypassable fallback: an argument that still exists is an argument something
    can still rely on. An authorization boundary must not be reachable from
    model output at all (KNOWN_LIMITATIONS 24, Class C).
    """


class Card(BaseModel):
    card_id: str
    issuer: str
    card_name: str
    network: str
    reward_currency: str
    # Rule Engine card_key for this card, or None when the engine has no verified
    # rule file for it. The Planner uses this to drive CompareCards/CalculateEarn
    # against the card the user actually holds (2026-07-22).
    card_key: str | None = None
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
