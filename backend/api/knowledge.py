"""Knowledge search route (BUILD_SPEC §9).

    GET /api/v1/knowledge/search?q=...

Direct hybrid retrieval — the debug view and the UI "sources" panel. It returns
the same `RetrievedChunk` list the Planner's SearchKnowledge tool produces, so
what the UI shows as a source is exactly what the recommender would retrieve.

JWT-protected like everything except /health and the auth routes, even though
the corpus is not user-specific: retrieval touches the LLM-adjacent surface and
should not be an unauthenticated scraping endpoint. The `q` parameter is
required and validated — an empty query is a 422, not an empty result set that
looks like "nothing matched".
"""

import uuid

from fastapi import APIRouter, Depends, Query, Request

from backend.api.responses import ok
from backend.application import knowledge as service
from backend.auth.dependencies import current_user_id

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

DOC_TYPES = ("reward_rules", "transfer_rules", "promotions", "benefit_guides", "issuer_policies")


@router.get("/search")
def search_knowledge(
    request: Request,
    q: str = Query(min_length=1, description="search query"),
    issuer: str | None = Query(default=None),
    program: str | None = Query(default=None),
    doc_type: str | None = Query(default=None, description=f"one of {DOC_TYPES}"),
    k: int = Query(default=5, ge=1, le=20),
    _user_id: uuid.UUID = Depends(current_user_id),
):
    result = service.search(q, issuer=issuer, program=program, doc_type=doc_type, k=k)
    return ok(request, result)
