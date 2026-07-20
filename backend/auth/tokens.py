"""Supabase JWT verification (BUILD_SPEC §1, §9).

Supabase issues the token; this process only verifies it. Every check that
could be skipped is a way in, so none are optional:

- signature, against the project's current signing key
- `exp`, enforced by PyJWT
- `aud == "authenticated"`, so a token minted for another audience (a service
  role key, an anon token) cannot be replayed as a user session
- `sub` present and a UUID, since it becomes `users.user_id`

**Two signing schemes, because Supabase changed theirs.** BUILD_SPEC §12
specifies `SUPABASE_JWT_SECRET`, which is the legacy symmetric scheme (HS256).
Supabase projects now migrate to asymmetric **JWT Signing Keys** — ES256 over
P-256 — published at `/auth/v1/.well-known/jwks.json`, and after migration the
legacy secret verifies nothing that is still valid. A project on either scheme
must work, so the algorithm in the token header selects the key source:

    HS256  -> SUPABASE_JWT_SECRET      (legacy projects)
    ES256  -> JWKS public key by `kid` (migrated projects)

**On reading the header before verifying.** `alg` comes from the untrusted
token, which is how algorithm-confusion attacks start. Two things make it safe
here: `ALGORITHMS_BY_SCHEME` is a closed allowlist, so `none` or `RS256` is
rejected outright; and the two schemes never share key material — HS256 is
verified only against the shared secret, never against a JWKS public key. The
classic attack (sign HS256 using the public key as the HMAC secret) requires
the server to feed a public key into HMAC, which never happens below.

A missing key raises rather than degrading to an unverified decode. A build
that accepts unsigned tokens when misconfigured is worse than one that refuses
to serve.
"""

import uuid
from dataclasses import dataclass
from functools import lru_cache

import jwt
from jwt import PyJWKClient

from backend.config.settings import get_settings

AUDIENCE = "authenticated"

LEGACY_ALGORITHM = "HS256"
ASYMMETRIC_ALGORITHMS = ("ES256",)
ALLOWED_ALGORITHMS = (LEGACY_ALGORITHM, *ASYMMETRIC_ALGORITHMS)


class AuthError(Exception):
    """Token missing, malformed, expired, or not ours. Mapped to HTTP 401."""


class AuthNotConfiguredError(RuntimeError):
    """No usable verification key — refuse to verify rather than skip it."""


@dataclass(frozen=True)
class TokenClaims:
    user_id: uuid.UUID
    email: str | None
    raw: dict


def jwks_url() -> str | None:
    base = get_settings().supabase_url
    return f"{base.rstrip('/')}/auth/v1/.well-known/jwks.json" if base else None


@lru_cache(maxsize=4)
def _jwk_client(url: str) -> PyJWKClient:
    """Cached per URL. PyJWKClient caches fetched keys internally, so a signing
    key is fetched once rather than on every request; a token whose `kid` is
    unknown triggers a refresh, which is what makes key rotation transparent."""
    return PyJWKClient(url, cache_keys=True)


def _verification_key(token: str) -> tuple[object, str]:
    """Resolve the key and the single algorithm permitted for this token."""
    try:
        algorithm = jwt.get_unverified_header(token).get("alg")
    except jwt.InvalidTokenError as exc:
        raise AuthError("malformed token header") from exc

    if algorithm not in ALLOWED_ALGORITHMS:
        raise AuthError(f"unsupported token algorithm: {algorithm!r}")

    if algorithm == LEGACY_ALGORITHM:
        secret = get_settings().supabase_jwt_secret
        if secret:
            return secret, algorithm
        if jwks_url():
            # The project verifies against JWT signing keys, so an HS256 token
            # cannot be one of ours whatever it is signed with. Reject it as a
            # bad token, not as a broken server.
            #
            # This is the path a Supabase `anon` or `service_role` API key takes:
            # both are real credentials for Supabase's own REST API and legacy
            # HS256 JWTs, and neither is ever a user session here. Reporting 503
            # would let anyone holding a public API key raise a server-fault
            # alert, and would blame us for a credential the caller chose.
            raise AuthError("token uses an unsupported legacy signing scheme")
        raise AuthNotConfiguredError(
            "token is signed with the legacy HS256 scheme, but neither "
            "SUPABASE_JWT_SECRET nor SUPABASE_URL is set, so there is no way to "
            "verify any token. Refusing to accept it unverified."
        )

    url = jwks_url()
    if not url:
        raise AuthNotConfiguredError(
            "token is signed with an asymmetric JWT signing key but SUPABASE_URL "
            "is not set, so the JWKS endpoint cannot be resolved."
        )
    try:
        return _jwk_client(url).get_signing_key_from_jwt(token).key, algorithm
    except jwt.exceptions.PyJWKClientError as exc:
        # Unknown `kid` or unreachable JWKS. Not a client error the caller can
        # fix by retrying with a different token, but also not something to
        # wave through.
        raise AuthError("token signing key could not be resolved") from exc


def verify_token(token: str) -> TokenClaims:
    key, algorithm = _verification_key(token)
    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=[algorithm],
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
