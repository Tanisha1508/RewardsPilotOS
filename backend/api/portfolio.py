"""Portfolio, cards, balances, and loyalty routes (BUILD_SPEC §9).

Routers do three things and no more: read the authenticated user, validate the
body against a DTO, and call the application layer. No queries, no ownership
checks, no reward logic — those belong to `backend/application/` and, for
anything involving reward math, to `rules/` and `graph/` (BUILD_SPEC §3).
"""

import uuid

from fastapi import APIRouter, Depends, Request

from backend.api.responses import ok
from backend.application import portfolio as service
from backend.auth.dependencies import current_user_id
from backend.schemas.portfolio import (
    BalanceIn,
    BalanceOut,
    CardIn,
    CardOut,
    CardPatch,
    LoyaltyIn,
    LoyaltyOut,
    PortfolioIn,
    PortfolioOut,
)
from contracts.api.envelope import Deleted

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


@router.get("")
def read_portfolio(request: Request, user_id: uuid.UUID = Depends(current_user_id)):
    portfolio, cards = service.get_portfolio(user_id)
    return ok(
        request,
        PortfolioOut(
            portfolio_id=portfolio.portfolio_id,
            portfolio_name=portfolio.portfolio_name,
            cards=[CardOut.model_validate(c) for c in cards],
        ),
    )


@router.post("")
def create_portfolio(
    request: Request, body: PortfolioIn, user_id: uuid.UUID = Depends(current_user_id)
):
    portfolio = service.create_portfolio(user_id, body.portfolio_name)
    return ok(
        request,
        PortfolioOut(
            portfolio_id=portfolio.portfolio_id,
            portfolio_name=portfolio.portfolio_name,
            cards=[],
        ),
    )


@router.get("/cards")
def list_cards(request: Request, user_id: uuid.UUID = Depends(current_user_id)):
    return ok(request, [CardOut.model_validate(c) for c in service.list_cards(user_id)])


@router.post("/cards")
def add_card(request: Request, body: CardIn, user_id: uuid.UUID = Depends(current_user_id)):
    card = service.add_card(user_id, **body.model_dump())
    return ok(request, CardOut.model_validate(card))


@router.patch("/cards/{card_id}")
def update_card(
    request: Request,
    card_id: uuid.UUID,
    body: CardPatch,
    user_id: uuid.UUID = Depends(current_user_id),
):
    # exclude_unset: PATCH applies only the fields the client actually sent.
    # Without it, every omitted field would be written back as null.
    card = service.update_card(user_id, card_id, **body.model_dump(exclude_unset=True))
    return ok(request, CardOut.model_validate(card))


@router.delete("/cards/{card_id}")
def delete_card(
    request: Request, card_id: uuid.UUID, user_id: uuid.UUID = Depends(current_user_id)
):
    service.delete_card(user_id, card_id)
    return ok(request, Deleted(id=str(card_id)))


@router.get("/balances")
def list_balances(request: Request, user_id: uuid.UUID = Depends(current_user_id)):
    return ok(request, [BalanceOut.from_model(b) for b in service.get_balances(user_id)])


@router.put("/balances/{card_id}")
def put_balance(
    request: Request,
    card_id: uuid.UUID,
    body: BalanceIn,
    user_id: uuid.UUID = Depends(current_user_id),
):
    balance = service.set_balance(
        user_id, card_id, body.reward_currency, body.current_balance, body.expiry_date
    )
    return ok(request, BalanceOut.from_model(balance))


@router.get("/loyalty")
def list_loyalty(request: Request, user_id: uuid.UUID = Depends(current_user_id)):
    return ok(request, [LoyaltyOut.from_model(a) for a in service.list_loyalty(user_id)])


@router.put("/loyalty")
def put_loyalty(request: Request, body: LoyaltyIn, user_id: uuid.UUID = Depends(current_user_id)):
    account = service.set_loyalty(
        user_id, body.program_name, body.program_type, body.balance, body.status_tier
    )
    return ok(request, LoyaltyOut.from_model(account))
