"""Chat and recommendation routes (BUILD_SPEC §9).

    POST /api/v1/chat                          run the workflow, persist, return
    GET  /api/v1/recommendations               history, newest first
    GET  /api/v1/recommendations/{id}          one (marks viewed)
    POST /api/v1/recommendations/{id}/feedback accepted | rejected | saved

Routers stay thin: authenticate, validate, delegate. The reasoning is the
workflow's and the numbers are the engines' — no business logic here.
"""

import uuid

from fastapi import APIRouter, Depends, Query, Request

from backend.api.responses import ok
from backend.application import chat as chat_service
from backend.application import recommendations as rec_service
from backend.auth.dependencies import current_user_id
from backend.schemas.chat import ChatIn, FeedbackIn, RecommendationOut

chat_router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
rec_router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@chat_router.post("")
def chat(request: Request, body: ChatIn, user_id: uuid.UUID = Depends(current_user_id)):
    row = chat_service.run_chat(user_id, body.query)
    return ok(request, RecommendationOut.from_model(row))


@rec_router.get("")
def list_recommendations(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    user_id: uuid.UUID = Depends(current_user_id),
):
    rows = rec_service.list_recommendations(user_id, limit)
    return ok(request, [RecommendationOut.from_model(r) for r in rows])


@rec_router.get("/{rec_id}")
def get_recommendation(
    request: Request, rec_id: uuid.UUID, user_id: uuid.UUID = Depends(current_user_id)
):
    row = rec_service.get_recommendation(user_id, rec_id)
    return ok(request, RecommendationOut.from_model(row))


@rec_router.post("/{rec_id}/feedback")
def feedback(
    request: Request,
    rec_id: uuid.UUID,
    body: FeedbackIn,
    user_id: uuid.UUID = Depends(current_user_id),
):
    row = rec_service.record_feedback(user_id, rec_id, body.status)
    return ok(request, RecommendationOut.from_model(row))
