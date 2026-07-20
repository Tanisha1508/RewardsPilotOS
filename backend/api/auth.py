"""Auth routes (BUILD_SPEC §9).

Exempt from `JWTAuthMiddleware` but not from verification: both routes depend
on `verified_claims`, which verifies the token itself. The exemption exists
because `/auth/sync` must work for a user whose local row does not exist yet.
"""

from fastapi import APIRouter, Depends, Request

from backend.api.responses import ok
from backend.application.errors import NotFoundError
from backend.application.users import get_user, sync_user
from backend.auth.dependencies import verified_claims
from backend.auth.tokens import TokenClaims
from backend.schemas.identity import SyncIn, UserOut

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/sync")
def sync(request: Request, body: SyncIn, claims: TokenClaims = Depends(verified_claims)):
    """Upsert the local mirror of the Supabase user. Idempotent: called after
    every login, not only signup."""
    user = sync_user(claims.user_id, claims.email, body.name)
    return ok(request, UserOut.model_validate(user))


@router.get("/me")
def me(request: Request, claims: TokenClaims = Depends(verified_claims)):
    user = get_user(claims.user_id)
    if user is None:
        raise NotFoundError("no local user row — call POST /api/v1/auth/sync first")
    return ok(request, UserOut.model_validate(user))
