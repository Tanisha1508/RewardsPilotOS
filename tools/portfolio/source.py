"""Where portfolio tools get their data.

The tool handlers have spec'd signatures — `get_cards(args: UserScopedInput)` —
with no room for a repository parameter, and changing them is a contract change
(Build Constraints). So the data source is resolved rather than injected, using
the same Protocol-plus-fake shape `rules/engine/cap_store.py` already
establishes for cap usage.

**Postgres is the default.** There is no fixture fallback in this module: an
unconfigured database raises rather than quietly answering from seed data.
Answering a real question with demo balances is exactly the fabrication the
project's first hard rule forbids — and it would look like a working system.

`InMemoryPortfolioSource` exists for the test suite and the evaluation harness,
which install it explicitly. The fixture *data* it carries lives in
`database/seed/demo_portfolio.json` (BUILD_SPEC §2), not here.
"""

import json
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Protocol

from sqlalchemy import select

from backend.models.identity import Goal
from backend.models.portfolio import Card as CardRow
from backend.models.portfolio import Portfolio as PortfolioRow
from backend.models.portfolio import RewardBalance as BalanceRow
from contracts.tools.portfolio import (
    Card,
    GetCardsOutput,
    GetPortfolioOutput,
    GetRewardBalancesOutput,
    GetTravelGoalsOutput,
    RewardBalance,
    TravelGoal,
)
from database.postgres.session import session_scope

SEED_PATH = Path(__file__).resolve().parents[2] / "database" / "seed" / "demo_portfolio.json"


class UnknownUserError(Exception):
    """No portfolio for this user id. Distinct from "an empty portfolio"."""


class PortfolioSource(Protocol):
    def portfolio(self, user_id: str) -> GetPortfolioOutput: ...

    def cards(self, user_id: str) -> GetCardsOutput: ...

    def balances(self, user_id: str) -> GetRewardBalancesOutput: ...

    def goals(self, user_id: str) -> GetTravelGoalsOutput: ...


# --------------------------------------------------------------------------
# Ambient user
#
# `RedemptionOptionsInput` documents that when `portfolio` is omitted "the tool
# loads the user's current balances itself" — but the input carries no user id,
# so there is nothing in the call to say whose. Rather than change a spec'd tool
# contract, the caller establishes the user for the scope of the request, the
# same way the database session is made ambient.
# --------------------------------------------------------------------------

_current_user: ContextVar[str | None] = ContextVar("portfolio_user", default=None)


@contextmanager
def acting_as(user_id: str):
    token = _current_user.set(user_id)
    try:
        yield user_id
    finally:
        _current_user.reset(token)


def current_user() -> str:
    user_id = _current_user.get()
    if user_id is None:
        raise UnknownUserError(
            "no user in context — a tool that loads the caller's own data must be "
            "invoked inside `acting_as(user_id)`."
        )
    return user_id


class PostgresPortfolioSource:
    """Reads the spec'd tables. A user id that is not a UUID cannot be a
    Supabase subject, so it fails loudly instead of returning nothing."""

    def _uuid(self, user_id: str) -> uuid.UUID:
        try:
            return uuid.UUID(user_id)
        except ValueError as exc:
            raise UnknownUserError(f"not a valid user id: {user_id!r}") from exc

    def _portfolio_row(self, session, user_id: str) -> PortfolioRow:
        row = session.scalars(
            select(PortfolioRow)
            .where(PortfolioRow.user_id == self._uuid(user_id))
            .order_by(PortfolioRow.created_at)
        ).first()
        if row is None:
            raise UnknownUserError(f"no portfolio for user {user_id}")
        return row

    def _cards(self, session, portfolio_id) -> list[Card]:
        rows = session.scalars(
            select(CardRow).where(CardRow.portfolio_id == portfolio_id).order_by(CardRow.card_name)
        )
        return [
            Card(
                card_id=str(row.card_id),
                issuer=row.issuer,
                card_name=row.card_name,
                network=row.network,
                # Read straight from the row since 2026-07-20. It used to be
                # derived from (issuer, card_name), which meant every new issuer
                # needed a code change and, without one, resolved to a currency
                # no graph node matched.
                reward_currency=row.reward_currency,
                status=row.status,
                annual_fee=float(row.annual_fee) if row.annual_fee is not None else None,
                renewal_date=row.renewal_date.isoformat() if row.renewal_date else None,
            )
            for row in rows
        ]

    def portfolio(self, user_id: str) -> GetPortfolioOutput:
        with session_scope() as session:
            row = self._portfolio_row(session, user_id)
            return GetPortfolioOutput(
                portfolio_id=str(row.portfolio_id),
                portfolio_name=row.portfolio_name,
                user_id=user_id,
                cards=self._cards(session, row.portfolio_id),
            )

    def cards(self, user_id: str) -> GetCardsOutput:
        with session_scope() as session:
            row = self._portfolio_row(session, user_id)
            return GetCardsOutput(cards=self._cards(session, row.portfolio_id))

    def balances(self, user_id: str) -> GetRewardBalancesOutput:
        with session_scope() as session:
            row = self._portfolio_row(session, user_id)
            rows = session.scalars(
                select(BalanceRow)
                .join(CardRow, CardRow.card_id == BalanceRow.card_id)
                .where(CardRow.portfolio_id == row.portfolio_id)
                .order_by(BalanceRow.reward_currency)
            )
            return GetRewardBalancesOutput(
                balances=[
                    RewardBalance(
                        card_id=str(b.card_id),
                        reward_currency=b.reward_currency,
                        current_balance=float(b.current_balance),
                        expiry_date=b.expiry_date.isoformat() if b.expiry_date else None,
                        last_updated=b.last_updated.date().isoformat(),
                    )
                    for b in rows
                ]
            )

    def goals(self, user_id: str) -> GetTravelGoalsOutput:
        with session_scope() as session:
            rows = session.scalars(
                select(Goal).where(Goal.user_id == self._uuid(user_id)).order_by(Goal.target_date)
            )
            return GetTravelGoalsOutput(
                goals=[
                    TravelGoal(
                        goal_id=str(g.goal_id),
                        goal_type=g.goal_type,
                        description=g.description,
                        target_date=g.target_date.isoformat() if g.target_date else None,
                        status=g.status,
                        # `goals` has no target_program / required_points column
                        # (BUILD_SPEC §4). Left unknown rather than parsed out of
                        # the description — see [NEED] in VERIFICATION_QUEUE.
                        target_program=None,
                        required_points=None,
                    )
                    for g in rows
                ]
            )


class InMemoryPortfolioSource:
    """Seeded fake for tests and the evaluation harness. Never the default."""

    def __init__(self, seed: dict) -> None:
        self._user_id = seed["user_id"]
        self._portfolio_id = seed["portfolio_id"]
        self._portfolio_name = seed["portfolio_name"]
        self._cards = [
            Card(**{k: v for k, v in c.items() if not k.startswith("_")}) for c in seed["cards"]
        ]
        self._balances = [RewardBalance(**b) for b in seed["balances"]]
        self._goals = [TravelGoal(**g) for g in seed["goals"]]

    def portfolio(self, user_id: str) -> GetPortfolioOutput:
        return GetPortfolioOutput(
            portfolio_id=self._portfolio_id,
            portfolio_name=self._portfolio_name,
            user_id=user_id,
            cards=self._cards,
        )

    def cards(self, user_id: str) -> GetCardsOutput:
        return GetCardsOutput(cards=self._cards)

    def balances(self, user_id: str) -> GetRewardBalancesOutput:
        return GetRewardBalancesOutput(balances=self._balances)

    def goals(self, user_id: str) -> GetTravelGoalsOutput:
        return GetTravelGoalsOutput(goals=self._goals)


def load_seed(path: Path = SEED_PATH) -> dict:
    return json.loads(path.read_text())


_source: PortfolioSource | None = None


def get_source() -> PortfolioSource:
    global _source
    if _source is None:
        _source = PostgresPortfolioSource()
    return _source


def set_source(source: PortfolioSource | None) -> None:
    """Install a source (tests, evaluation). `None` restores the default."""
    global _source
    _source = source
