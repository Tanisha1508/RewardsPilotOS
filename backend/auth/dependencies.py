"""FastAPI auth dependencies.

`current_user_id` reads what the middleware already verified. `verified_claims`
verifies a token directly and is used by the auth routes, which the middleware
skips — `/auth/sync` has to accept a valid token for a user who has no local
row yet, which is the whole point of the endpoint.
"""

import uuid

from fastapi import Header, Request

from backend.auth.tokens import AuthError, TokenClaims, bearer_token, verify_token


def current_user_id(request: Request) -> uuid.UUID:
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        # Reachable only if a route is mounted outside the middleware's guarded
        # prefix. Failing closed beats serving another user's data.
        raise AuthError("request reached a protected route without authentication")
    return user_id


def verified_claims(authorization: str | None = Header(default=None)) -> TokenClaims:
    return verify_token(bearer_token(authorization))
