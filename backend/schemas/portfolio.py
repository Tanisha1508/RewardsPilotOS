"""HTTP DTOs for the portfolio endpoints (BUILD_SPEC §3: `backend/schemas`
holds HTTP request/response shapes only — no domain logic, no ORM types).

These are separate from `contracts/tools/portfolio.py` on purpose. The tool
contracts describe what the agent's tools return; these describe what the HTTP
API accepts and returns. They overlap today, and coupling them would mean a UI
field change forcing a change in what the Planner sees.

`PATCH` uses sentinel-free optional fields plus `exclude_unset`, so "field
omitted" and "field explicitly set to null" stay distinguishable.
"""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CardIn(BaseModel):
    issuer: str = Field(min_length=1, max_length=100)
    card_name: str = Field(min_length=1, max_length=200)
    network: str = Field(min_length=1, max_length=50)
    # Required, with no default. A card's reward currency is the key that links
    # it to the transfer graph; defaulting it would mean guessing, and a wrong
    # guess resolves to the wrong graph node rather than failing.
    reward_currency: str = Field(min_length=1, max_length=100)
    joining_date: date | None = None
    annual_fee: float | None = Field(default=None, ge=0)
    renewal_date: date | None = None
    status: str = "active"


class CardPatch(BaseModel):
    issuer: str | None = Field(default=None, min_length=1, max_length=100)
    card_name: str | None = Field(default=None, min_length=1, max_length=200)
    network: str | None = Field(default=None, min_length=1, max_length=50)
    reward_currency: str | None = Field(default=None, min_length=1, max_length=100)
    joining_date: date | None = None
    annual_fee: float | None = Field(default=None, ge=0)
    renewal_date: date | None = None
    status: str | None = None


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    card_id: uuid.UUID
    issuer: str
    card_name: str
    network: str
    reward_currency: str
    card_key: str | None = None
    joining_date: date | None = None
    annual_fee: float | None = None
    renewal_date: date | None = None
    status: str


class PortfolioIn(BaseModel):
    portfolio_name: str = Field(min_length=1, max_length=200)


class PortfolioOut(BaseModel):
    portfolio_id: uuid.UUID
    portfolio_name: str
    cards: list[CardOut] = Field(default_factory=list)


class BalanceIn(BaseModel):
    reward_currency: str = Field(min_length=1, max_length=100)
    # ge=0: a negative reward balance is not a thing, and accepting one would
    # feed a wrong number straight into redemption planning.
    current_balance: float = Field(ge=0)
    expiry_date: date | None = None


class BalanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    balance_id: uuid.UUID
    card_id: uuid.UUID
    reward_currency: str
    current_balance: float
    expiry_date: date | None = None
    last_updated: str

    @classmethod
    def from_model(cls, row) -> "BalanceOut":
        return cls(
            balance_id=row.balance_id,
            card_id=row.card_id,
            reward_currency=row.reward_currency,
            current_balance=float(row.current_balance),
            expiry_date=row.expiry_date,
            last_updated=row.last_updated.isoformat(),
        )


class LoyaltyIn(BaseModel):
    program_name: str = Field(min_length=1, max_length=200)
    program_type: str = Field(pattern="^(airline|hotel)$")
    balance: float = Field(default=0, ge=0)
    status_tier: str | None = None


class LoyaltyOut(BaseModel):
    loyalty_id: uuid.UUID
    program_name: str
    program_type: str
    balance: float
    status_tier: str | None = None
    last_updated: str

    @classmethod
    def from_model(cls, row) -> "LoyaltyOut":
        return cls(
            loyalty_id=row.loyalty_id,
            program_name=row.program_name,
            program_type=row.program_type,
            balance=float(row.balance),
            status_tier=row.status_tier,
            last_updated=row.last_updated.isoformat(),
        )
