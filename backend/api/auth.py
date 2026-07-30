"""Auth routes (BUILD_SPEC §9).

Exempt from `JWTAuthMiddleware` but not from verification: both routes depend
on `verified_claims`, which verifies the token itself. The exemption exists
because `/auth/sync` must work for a user whose local row does not exist yet.
"""

from fastapi import APIRouter, Depends, Request

from backend.api.responses import ok
from backend.application.errors import NotFoundError
from backend.application.users import delete_user, get_user, sync_user
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


@router.delete("/me")
def delete_me(request: Request, claims: TokenClaims = Depends(verified_claims)):
    """Erase everything this service holds about the caller (privacy audit P3).

    Scoped to the token's own `sub` — there is no id parameter, so this route
    cannot be pointed at anyone else even by a caller who tries.

    Deletes the local data only. The Supabase auth identity survives (it needs
    the service-role key, which this service does not hold), so signing in again
    produces a fresh empty account rather than restoring anything.
    """
    delete_user(claims.user_id)
    return ok(request, {"deleted": True})
