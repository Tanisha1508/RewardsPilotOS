"""API shape that holds without a database: the envelope, the public/protected
split, and honest reporting when Postgres is not configured.

These run everywhere. The CRUD behaviour behind them needs a real database and
lives in `tests/integration/`, which skips unless TEST_DATABASE_URL is set.
"""

import pytest
from fastapi.testclient import TestClient

from backend.config.settings import get_settings
from backend.main import create_app
from backend.middleware.auth import is_public
from tests.unit.test_auth_tokens import SECRET, make_token


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    with TestClient(create_app(), raise_server_exceptions=False) as test_client:
        yield test_client
    get_settings.cache_clear()


def envelope_shape(payload: dict) -> bool:
    return (
        set(payload) == {"data", "error", "meta"}
        and set(payload["meta"]) == {"request_id", "generated_at"}
        and bool(payload["meta"]["request_id"])
    )


def test_health_is_public_and_enveloped(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert envelope_shape(response.json())


def test_health_reports_an_unconfigured_database_rather_than_ok(client):
    """A green health check for a database that was never contacted is the one
    lie that makes a health endpoint worse than useless."""
    checks = client.get("/api/v1/health").json()["data"]["checks"]
    assert checks["database"] == "not_configured"


def test_protected_route_without_a_token_is_401(client):
    response = client.get("/api/v1/portfolio")
    assert response.status_code == 401
    body = response.json()
    assert envelope_shape(body)
    assert body["data"] is None
    assert body["error"]["code"] == "unauthorized"


def test_error_responses_use_the_same_envelope_as_successes(client):
    """A client should never branch on response shape to find out which it got."""
    ok_body = client.get("/api/v1/health").json()
    err_body = client.get("/api/v1/portfolio").json()
    assert envelope_shape(ok_body) and envelope_shape(err_body)
    assert ok_body["error"] is None and err_body["data"] is None


def test_authenticated_request_without_a_database_reports_503_not_500(client):
    """Authentication succeeds, then the database is missing. That is a server
    configuration fault and should say so, not surface as an opaque 500."""
    response = client.get("/api/v1/portfolio", headers={"Authorization": f"Bearer {make_token()}"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "database_not_configured" or response.json()[
        "error"
    ]["message"].startswith("DATABASE_URL")


def test_request_id_is_echoed_when_supplied(client):
    response = client.get("/api/v1/health", headers={"x-request-id": "trace-me"})
    assert response.json()["meta"]["request_id"] == "trace-me"
    assert response.headers["x-request-id"] == "trace-me"


@pytest.mark.parametrize(
    "path,public",
    [
        ("/api/v1/health", True),
        ("/api/v1/auth/sync", True),
        ("/api/v1/auth/me", True),
        ("/api/v1/portfolio", False),
        ("/api/v1/portfolio/cards", False),
        ("/api/v1/preferences", False),
        ("/api/v1/goals", False),
        # The guard matches on prefix; these must not sneak through by looking
        # like a public path.
        ("/api/v1/healthcheck-internal", True),
        ("/api/v1/portfolio/auth/", False),
    ],
)
def test_public_path_allowlist(path, public):
    assert is_public(path) is public
