"""Supabase JWT verification (BUILD_SPEC §1, §9).

Supabase issues the token; this process only verifies it. Every check that
could be skipped is a way in, so none are optional:

- signature, against `SUPABASE_JWT_SECRET` (HS256, Supabase's symmetric scheme)
- `exp`, enforced by PyJWT
- `aud == "authenticated"`, so a token minted for another audience (a service
  role key, an anon token) cannot be replayed as a user session
- `sub` present and a UUID, since it becomes `users.user_id`

An unset secret raises rather than degrading to an unverified decode. A build
that accepts unsigned tokens when misconfigured is worse than one that refuses
to start.
"""

import uuid
from dataclasses import dataclass

import jwt

from backend.config.settings import get_settings

AUDIENCE = "authenticated"
ALGORITHM = "HS256"


class AuthError(Exception):
    """Token missing, malformed, expired, or not ours. Mapped to HTTP 401."""


class AuthNotConfiguredError(RuntimeError):
    """SUPABASE_JWT_SECRET is unset — refuse to verify rather than skip it."""


@dataclass(frozen=True)
class TokenClaims:
    user_id: uuid.UUID
    email: str | None
    raw: dict


def verify_token(token: str) -> TokenClaims:
    secret = get_settings().supabase_jwt_secret
    if not secret:
        raise AuthNotConfiguredError(
            "SUPABASE_JWT_SECRET is not set — refusing to accept tokens without "
            "verifying their signature."
        )
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[ALGORITHM],
            audience=AUDIENCE,
            options={"require": ["exp", "sub", "aud"]},
        )
    except jwt.InvalidTokenError as exc:
        # Deliberately not echoing the library's reason to the client: "signature
        # expired" vs "bad signature" tells an attacker which half they got right.
        raise AuthError("invalid or expired token") from exc

    try:
        user_id = uuid.UUID(str(claims["sub"]))
    except (KeyError, ValueError) as exc:
        raise AuthError("token subject is not a valid user id") from exc

    return TokenClaims(user_id=user_id, email=claims.get("email"), raw=claims)


def bearer_token(header_value: str | None) -> str:
    """Extract the token from an `Authorization: Bearer <token>` header."""
    if not header_value:
        raise AuthError("missing Authorization header")
    scheme, _, token = header_value.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AuthError("Authorization header must be 'Bearer <token>'")
    return token.strip()
