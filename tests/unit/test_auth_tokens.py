"""Supabase JWT verification (BUILD_SPEC §9).

Every test here is a way in that must stay shut. The interesting ones are not
"a good token works" but the four that a permissive implementation would let
through: no signature check, no expiry check, no audience check, and a subject
that is not a user id.
"""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from backend.auth.tokens import (
    AuthError,
    AuthNotConfiguredError,
    bearer_token,
    verify_token,
)
from backend.config.settings import get_settings

# >= 32 bytes: shorter HMAC keys are legal but PyJWT warns, and the warning is
# right — this mirrors the length Supabase actually issues.
SECRET = "test-jwt-secret-not-a-real-one-0123456789"
USER_ID = uuid.uuid4()


@pytest.fixture(autouse=True)
def configured_secret(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_token(
    secret=SECRET, *, sub=None, aud="authenticated", expires_in=3600, email=None, **extra
):
    subject = str(sub or USER_ID)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "aud": aud,
        "exp": now + timedelta(seconds=expires_in),
        "iat": now,
        # Derived from the subject, not a constant. `users.email` is UNIQUE — as
        # it should be, since two Supabase accounts cannot share an address — so
        # a fixed email here made the second user in any multi-user test fail to
        # sync, and the test then read the resulting 404 as "no cards".
        "email": email or f"{subject}@example.test",
        **extra,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_valid_token_yields_claims():
    claims = verify_token(make_token(email="user@example.test"))
    assert claims.user_id == USER_ID
    assert claims.email == "user@example.test"


def test_token_signed_with_another_secret_is_rejected():
    """The whole point of verification: anyone can mint a JWT."""
    with pytest.raises(AuthError):
        verify_token(make_token(secret="attacker-controlled-secret"))


def test_expired_token_is_rejected():
    with pytest.raises(AuthError):
        verify_token(make_token(expires_in=-60))


def test_token_for_another_audience_is_rejected():
    """A service-role or anon token is correctly signed by the same project —
    audience is what stops it being replayed as a user session."""
    with pytest.raises(AuthError):
        verify_token(make_token(aud="service_role"))


def test_token_without_expiry_is_rejected():
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": str(USER_ID), "aud": "authenticated", "iat": now}, SECRET, algorithm="HS256"
    )
    with pytest.raises(AuthError):
        verify_token(token)


def test_non_uuid_subject_is_rejected():
    """`sub` becomes users.user_id — a non-UUID subject would either error deep
    in a query or, worse, match nothing and look like an empty account."""
    with pytest.raises(AuthError):
        verify_token(make_token(sub="not-a-uuid"))


def test_missing_secret_raises_rather_than_skipping_verification(monkeypatch):
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    get_settings.cache_clear()
    # Not AuthError: this is a misconfigured server, not a bad client. It must
    # never degrade into accepting the token unverified.
    with pytest.raises(AuthNotConfiguredError):
        verify_token(make_token())


@pytest.mark.parametrize("header", [None, "", "token abc", "Bearer", "Bearer   ", "Basic abc123"])
def test_malformed_authorization_headers_are_rejected(header):
    with pytest.raises(AuthError):
        bearer_token(header)


def test_bearer_scheme_is_case_insensitive():
    assert bearer_token("bearer abc123") == "abc123"
