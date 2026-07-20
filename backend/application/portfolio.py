"""Portfolio, card, balance, and loyalty operations (BUILD_SPEC §9).

Every function takes `user_id` and every query is filtered by it. Ownership is
re-established from the database on each call rather than trusted from the
request: a card id in a URL is a claim, not proof. `_owned_card` is the single
place that check lives, so a new endpoint cannot forget it.
"""

import uuid
from datetime import date

from sqlalchemy import select

from backend.application.errors import NotFoundError, PermissionDeniedError
from backend.models.identity import User
from backend.models.portfolio import Card, LoyaltyAccount, Portfolio, RewardBalance
from database.postgres.session import session_scope


def _portfolio_for(session, user_id: uuid.UUID) -> Portfolio:
    portfolio = session.scalars(
        select(Portfolio).where(Portfolio.user_id == user_id).order_by(Portfolio.created_at)
    ).first()
    if portfolio is None:
        raise NotFoundError("no portfolio for this user — call POST /api/v1/auth/sync first")
    return portfolio


def _owned_card(session, user_id: uuid.UUID, card_id: uuid.UUID) -> Card:
    card = session.get(Card, card_id)
    if card is None:
        raise NotFoundError(f"card {card_id} not found")
    owner = session.scalars(
        select(Portfolio.user_id).where(Portfolio.portfolio_id == card.portfolio_id)
    ).first()
    if owner != user_id:
        raise PermissionDeniedError(f"card {card_id} not found")
    return card


def get_portfolio(user_id: uuid.UUID) -> tuple[Portfolio, list[Card]]:
    with session_scope() as session:
        portfolio = _portfolio_for(session, user_id)
        cards = list(
            session.scalars(
                select(Card)
                .where(Card.portfolio_id == portfolio.portfolio_id)
                .order_by(Card.card_name)
            )
        )
        return portfolio, cards


def create_portfolio(user_id: uuid.UUID, portfolio_name: str) -> Portfolio:
    with session_scope() as session:
        if session.get(User, user_id) is None:
            raise NotFoundError("unknown user — call POST /api/v1/auth/sync first")
        portfolio = Portfolio(user_id=user_id, portfolio_name=portfolio_name)
        session.add(portfolio)
        session.flush()
        return portfolio


def list_cards(user_id: uuid.UUID) -> list[Card]:
    return get_portfolio(user_id)[1]


def add_card(
    user_id: uuid.UUID,
    issuer: str,
    card_name: str,
    network: str,
    reward_currency: str,
    joining_date: date | None = None,
    annual_fee: float | None = None,
    renewal_date: date | None = None,
    status: str = "active",
) -> Card:
    with session_scope() as session:
        portfolio = _portfolio_for(session, user_id)
        card = Card(
            portfolio_id=portfolio.portfolio_id,
            issuer=issuer,
            card_name=card_name,
            network=network,
            reward_currency=reward_currency,
            joining_date=joining_date,
            annual_fee=annual_fee,
            renewal_date=renewal_date,
            status=status,
        )
        session.add(card)
        session.flush()
        return card


def update_card(user_id: uuid.UUID, card_id: uuid.UUID, **changes) -> Card:
    with session_scope() as session:
        card = _owned_card(session, user_id, card_id)
        # PATCH semantics: an omitted field is "leave it alone", which is not
        # the same as an explicit null, so unset values never reach here.
        for field, value in changes.items():
            setattr(card, field, value)
        session.flush()
        return card


def delete_card(user_id: uuid.UUID, card_id: uuid.UUID) -> None:
    with session_scope() as session:
        card = _owned_card(session, user_id, card_id)
        session.delete(card)


def get_balances(user_id: uuid.UUID) -> list[RewardBalance]:
    with session_scope() as session:
        portfolio = _portfolio_for(session, user_id)
        return list(
            session.scalars(
                select(RewardBalance)
                .join(Card, Card.card_id == RewardBalance.card_id)
                .where(Card.portfolio_id == portfolio.portfolio_id)
                .order_by(RewardBalance.reward_currency)
            )
        )


def set_balance(
    user_id: uuid.UUID,
    card_id: uuid.UUID,
    reward_currency: str,
    current_balance: float,
    expiry_date: date | None = None,
) -> RewardBalance:
    """Upsert the balance for one card and currency.

    PUT, not POST: a card holds one balance per reward currency, and a user
    correcting a number they typed wrong should not create a second row that
    the reader then has to choose between.
    """
    with session_scope() as session:
        _owned_card(session, user_id, card_id)
        balance = session.scalars(
            select(RewardBalance).where(
                RewardBalance.card_id == card_id,
                RewardBalance.reward_currency == reward_currency,
            )
        ).first()
        if balance is None:
            balance = RewardBalance(
                card_id=card_id,
                reward_currency=reward_currency,
                current_balance=current_balance,
                expiry_date=expiry_date,
            )
            session.add(balance)
        else:
            balance.current_balance = current_balance
            balance.expiry_date = expiry_date
        session.flush()
        return balance


def list_loyalty(user_id: uuid.UUID) -> list[LoyaltyAccount]:
    with session_scope() as session:
        portfolio = _portfolio_for(session, user_id)
        return list(
            session.scalars(
                select(LoyaltyAccount)
                .where(LoyaltyAccount.portfolio_id == portfolio.portfolio_id)
                .order_by(LoyaltyAccount.program_name)
            )
        )


def set_loyalty(
    user_id: uuid.UUID,
    program_name: str,
    program_type: str,
    balance: float,
    status_tier: str | None = None,
) -> LoyaltyAccount:
    """Upsert by program name, for the same reason `set_balance` upserts."""
    with session_scope() as session:
        portfolio = _portfolio_for(session, user_id)
        account = session.scalars(
            select(LoyaltyAccount).where(
                LoyaltyAccount.portfolio_id == portfolio.portfolio_id,
                LoyaltyAccount.program_name == program_name,
            )
        ).first()
        if account is None:
            account = LoyaltyAccount(
                portfolio_id=portfolio.portfolio_id,
                program_name=program_name,
                program_type=program_type,
                balance=balance,
                status_tier=status_tier,
            )
            session.add(account)
        else:
            account.program_type = program_type
            account.balance = balance
            account.status_tier = status_tier
        session.flush()
        return account
