"""Asymmetric Supabase JWT signing keys (ES256).

Supabase projects migrate from a shared HS256 secret to per-project ES256
signing keys published as JWKS. After migration the legacy secret verifies
nothing still valid, so an HS256-only backend rejects every real login — which
is what this project's own Supabase instance would have done.

The attack these tests exist for is algorithm confusion: the `alg` field is
attacker-controlled, so a verifier that trusts it can be talked into using the
wrong key, or none at all.
"""

import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from backend.auth import tokens as tokens_module
from backend.auth.tokens import AuthError, AuthNotConfiguredError, verify_token
from backend.config.settings import get_settings
from tests.unit.test_auth_tokens import SECRET

USER_ID = uuid.uuid4()
SUPABASE_URL = "https://project.supabase.test"


@pytest.fixture()
def signing_key():
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(autouse=True)
def configured(monkeypatch, signing_key):
    """Point the verifier at an in-process key instead of the network."""
    monkeypatch.setenv("SUPABASE_URL", SUPABASE_URL)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    get_settings.cache_clear()

    class FakeKey:
        key = signing_key.public_key()

    class FakeJWKClient:
        def __init__(self, *args, **kwargs):
            pass

        def get_signing_key_from_jwt(self, token):
            return FakeKey()

    tokens_module._jwk_client.cache_clear()
    monkeypatch.setattr(tokens_module, "_jwk_client", lambda url: FakeJWKClient())
    yield
    get_settings.cache_clear()


def _b64(payload: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()


def es256_token(key, *, sub=None, aud="authenticated", expires_in=3600):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(sub or USER_ID),
            "aud": aud,
            "exp": now + timedelta(seconds=expires_in),
            "iat": now,
            "email": "user@example.test",
        },
        key,
        algorithm="ES256",
        headers={"kid": "0b338be3-f7e9-4312-80e4-7f5577e2b9ea"},
    )


def test_es256_token_is_accepted(signing_key):
    """The case that was broken: a token from a migrated Supabase project."""
    claims = verify_token(es256_token(signing_key))
    assert claims.user_id == USER_ID


def test_es256_token_signed_by_another_key_is_rejected():
    attacker_key = ec.generate_private_key(ec.SECP256R1())
    with pytest.raises(AuthError):
        verify_token(es256_token(attacker_key))


def test_expired_es256_token_is_rejected(signing_key):
    with pytest.raises(AuthError):
        verify_token(es256_token(signing_key, expires_in=-60))


def test_es256_token_for_another_audience_is_rejected(signing_key):
    with pytest.raises(AuthError):
        verify_token(es256_token(signing_key, aud="service_role"))


def test_hs256_still_works_for_projects_on_the_legacy_secret():
    """The spec'd scheme must keep working — a project that has not migrated
    still signs with the shared secret."""
    from tests.unit.test_auth_tokens import make_token

    assert verify_token(make_token(sub=USER_ID)).user_id == USER_ID


def test_alg_none_is_rejected(signing_key):
    """The oldest JWT attack: strip the signature and claim no algorithm."""
    token = jwt.encode({"sub": str(USER_ID), "aud": "authenticated"}, None, algorithm="none")
    with pytest.raises(AuthError):
        verify_token(token)


def test_public_key_cannot_be_used_as_an_hmac_secret(signing_key):
    """Algorithm confusion, the reason `alg` is never allowed to choose the key
    source freely: an attacker signs HS256 using the *public* key as the shared
    secret, hoping the server feeds it into HMAC. Here HS256 is only ever
    verified against SUPABASE_JWT_SECRET, so the forgery fails."""
    public_pem = signing_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    # Built by hand: PyJWT refuses to *encode* HS256 with an asymmetric key, so
    # the forgery cannot be produced with jwt.encode. A real attacker has no
    # such scruples, which is exactly why the check must live in the verifier.
    exp = int((datetime.now(timezone.utc) + timedelta(seconds=3600)).timestamp())
    header = _b64({"alg": "HS256", "typ": "JWT"})
    payload = _b64({"sub": str(USER_ID), "aud": "authenticated", "exp": exp})
    signature = base64.urlsafe_b64encode(
        hmac.new(public_pem, f"{header}.{payload}".encode(), hashlib.sha256).digest()
    ).rstrip(b"=")
    forged = f"{header}.{payload}.{signature.decode()}"

    with pytest.raises(AuthError):
        verify_token(forged)


def test_supabase_anon_key_is_rejected_as_unauthorized_not_misconfigured(monkeypatch):
    """A Supabase `anon` API key is a legacy HS256 JWT and a perfectly real
    credential — for Supabase's REST API, never as a user session here.

    Found by smoke-testing against the live project: it returned 503
    `auth_not_configured`, which blames the server for a credential the caller
    chose, and lets anyone holding a *public* API key trip server-fault alerts.
    On a project using JWT signing keys, an HS256 token simply is not ours.
    """
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    get_settings.cache_clear()

    anon_like = jwt.encode(
        {"iss": "supabase", "role": "anon", "aud": "authenticated"},
        "whatever-the-project-secret-is",
        algorithm="HS256",
    )
    with pytest.raises(AuthError):
        verify_token(anon_like)


def test_no_verification_path_at_all_is_a_misconfiguration(monkeypatch):
    """The genuine 503: neither scheme is configured, so nothing can be
    verified. Distinct from "this token is not ours"."""
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    get_settings.cache_clear()

    token = jwt.encode({"sub": str(USER_ID), "aud": "authenticated"}, "x", algorithm="HS256")
    with pytest.raises(AuthNotConfiguredError):
        verify_token(token)


def test_unsupported_algorithm_is_rejected(signing_key):
    """RS256 is a perfectly good algorithm and still not one we accept — the
    allowlist is closed, not "anything asymmetric"."""
    header = jwt.get_unverified_header(es256_token(signing_key))
    assert header["alg"] == "ES256"
    assert "RS256" not in tokens_module.ALLOWED_ALGORITHMS


def test_missing_supabase_url_raises_rather_than_skipping_verification(monkeypatch, signing_key):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    get_settings.cache_clear()
    with pytest.raises(AuthNotConfiguredError):
        verify_token(es256_token(signing_key))
