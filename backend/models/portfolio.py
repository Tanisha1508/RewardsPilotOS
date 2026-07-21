"""Portfolio, card, balance, and loyalty tables (BUILD_SPEC §4).

Balances are user-entered by design — there are no bank APIs (KNOWN_LIMITATIONS
item 1) — so `last_updated` is part of the answer, not bookkeeping: a
recommendation states how stale the number it used is.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, created_at_column, pk_uuid, updated_at_column


class Portfolio(Base):
    __tablename__ = "portfolios"

    portfolio_id: Mapped[uuid.UUID] = pk_uuid()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    portfolio_name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = created_at_column()


class Card(Base):
    __tablename__ = "cards"

    card_id: Mapped[uuid.UUID] = pk_uuid()
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("portfolios.portfolio_id", ondelete="CASCADE"), nullable=False, index=True
    )
    issuer: Mapped[str] = mapped_column(String(100), nullable=False)
    card_name: Mapped[str] = mapped_column(String(200), nullable=False)
    network: Mapped[str] = mapped_column(String(50), nullable=False)
    # Added 2026-07-20 (product-owner approved, closes KNOWN_LIMITATIONS item 17).
    # Must match a `graph_nodes.node_id` for transfer paths to resolve. It is not
    # a foreign key: a card can be tracked before its currency is registered in
    # the graph, and the graph tools report that gap explicitly rather than
    # returning empty paths.
    reward_currency: Mapped[str] = mapped_column(String(100), nullable=False)
    # Rule Engine card_key (rules/seed/<card_key>), resolved at creation from
    # (issuer, card_name). Nullable: a tracked card the engine has no verified
    # rule file for has NULL here — "tracked, not reasoned about" (2026-07-22).
    card_key: Mapped[str | None] = mapped_column(String(100))
    joining_date: Mapped[date | None] = mapped_column(Date)
    # Money: Numeric, never float. Annual fees are compared and displayed, and
    # binary floating point cannot represent 12500.00 exactly.
    annual_fee: Mapped[float | None] = mapped_column(Numeric(12, 2))
    renewal_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class RewardBalance(Base):
    __tablename__ = "reward_balances"

    balance_id: Mapped[uuid.UUID] = pk_uuid()
    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cards.card_id", ondelete="CASCADE"), nullable=False, index=True
    )
    reward_currency: Mapped[str] = mapped_column(String(100), nullable=False)
    current_balance: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    last_updated: Mapped[datetime] = updated_at_column()


class LoyaltyAccount(Base):
    __tablename__ = "loyalty_accounts"

    loyalty_id: Mapped[uuid.UUID] = pk_uuid()
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("portfolios.portfolio_id", ondelete="CASCADE"), nullable=False, index=True
    )
    program_name: Mapped[str] = mapped_column(String(200), nullable=False)
    program_type: Mapped[str] = mapped_column(String(20), nullable=False)  # airline|hotel
    balance: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    status_tier: Mapped[str | None] = mapped_column(String(100))
    last_updated: Mapped[datetime] = updated_at_column()
