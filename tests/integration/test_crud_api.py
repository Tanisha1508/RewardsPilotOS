"""CRUD endpoints against a real database (BUILD_SPEC §9).

The behaviours worth testing here are the ones a happy-path suite misses:
ownership isolation between two users, PATCH not nulling omitted fields, PUT
upserting rather than duplicating, and sync being idempotent.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from tests.unit.test_auth_tokens import make_token


@pytest.fixture()
def client(jwt_secret):
    with TestClient(create_app(), raise_server_exceptions=False) as test_client:
        yield test_client


def auth(user_id: uuid.UUID, secret: str) -> dict:
    return {"Authorization": f"Bearer {make_token(secret, sub=user_id)}"}


@pytest.fixture()
def synced_user(client, jwt_secret, user_id):
    response = client.post("/api/v1/auth/sync", json={}, headers=auth(user_id, jwt_secret))
    assert response.status_code == 200, response.text
    return user_id


def add_card(client, secret, user_id, **overrides) -> dict:
    body = {
        "issuer": "hdfc",
        "card_name": "HDFC Infinia",
        "network": "visa",
        "annual_fee": 12500.0,
        **overrides,
    }
    response = client.post("/api/v1/portfolio/cards", json=body, headers=auth(user_id, secret))
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_sync_creates_the_user_and_a_default_portfolio(client, jwt_secret, user_id):
    client.post("/api/v1/auth/sync", json={"name": "Tanisha"}, headers=auth(user_id, jwt_secret))
    response = client.get("/api/v1/portfolio", headers=auth(user_id, jwt_secret))
    assert response.status_code == 200
    assert response.json()["data"]["cards"] == []


def test_sync_is_idempotent(client, jwt_secret, user_id):
    """It runs after every login, not only signup."""
    first = client.post("/api/v1/auth/sync", json={}, headers=auth(user_id, jwt_secret))
    second = client.post("/api/v1/auth/sync", json={}, headers=auth(user_id, jwt_secret))
    assert first.status_code == second.status_code == 200
    assert first.json()["data"]["user_id"] == second.json()["data"]["user_id"]


def test_card_lifecycle(client, jwt_secret, synced_user):
    card = add_card(client, jwt_secret, synced_user)
    card_id = card["card_id"]

    listed = client.get("/api/v1/portfolio/cards", headers=auth(synced_user, jwt_secret))
    assert [c["card_id"] for c in listed.json()["data"]] == [card_id]

    deleted = client.delete(
        f"/api/v1/portfolio/cards/{card_id}", headers=auth(synced_user, jwt_secret)
    )
    assert deleted.status_code == 200
    after = client.get("/api/v1/portfolio/cards", headers=auth(synced_user, jwt_secret))
    assert after.json()["data"] == []


def test_patch_leaves_omitted_fields_alone(client, jwt_secret, synced_user):
    """The bug this catches: PATCH implemented with `model_dump()` instead of
    `model_dump(exclude_unset=True)` writes null over every field the client
    did not send."""
    card = add_card(client, jwt_secret, synced_user, renewal_date="2026-11-01")
    response = client.patch(
        f"/api/v1/portfolio/cards/{card['card_id']}",
        json={"card_name": "HDFC Infinia Metal"},
        headers=auth(synced_user, jwt_secret),
    )
    assert response.status_code == 200
    updated = response.json()["data"]
    assert updated["card_name"] == "HDFC Infinia Metal"
    assert updated["renewal_date"] == "2026-11-01"
    assert updated["annual_fee"] == 12500.0


def test_another_users_card_is_not_reachable(client, jwt_secret, synced_user, user_id):
    """Ownership is re-established from the database, never trusted from the
    URL. Reported as 404, not 403 — a 403 confirms the card exists."""
    card = add_card(client, jwt_secret, synced_user)
    intruder = uuid.uuid4()
    client.post("/api/v1/auth/sync", json={}, headers=auth(intruder, jwt_secret))

    response = client.patch(
        f"/api/v1/portfolio/cards/{card['card_id']}",
        json={"card_name": "stolen"},
        headers=auth(intruder, jwt_secret),
    )
    assert response.status_code == 404

    listed = client.get("/api/v1/portfolio/cards", headers=auth(intruder, jwt_secret))
    assert listed.json()["data"] == []


def test_balance_put_upserts_rather_than_duplicating(client, jwt_secret, synced_user):
    card = add_card(client, jwt_secret, synced_user)
    payload = {"reward_currency": "hdfc_reward_points", "current_balance": 48000}
    for balance in (48000, 51000):
        response = client.put(
            f"/api/v1/portfolio/balances/{card['card_id']}",
            json={**payload, "current_balance": balance},
            headers=auth(synced_user, jwt_secret),
        )
        assert response.status_code == 200

    balances = client.get(
        "/api/v1/portfolio/balances", headers=auth(synced_user, jwt_secret)
    ).json()["data"]
    assert len(balances) == 1
    assert balances[0]["current_balance"] == 51000


def test_negative_balance_is_rejected(client, jwt_secret, synced_user):
    card = add_card(client, jwt_secret, synced_user)
    response = client.put(
        f"/api/v1/portfolio/balances/{card['card_id']}",
        json={"reward_currency": "hdfc_reward_points", "current_balance": -5},
        headers=auth(synced_user, jwt_secret),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_loyalty_put_upserts_by_program(client, jwt_secret, synced_user):
    for tier in ("Silver", "Gold"):
        response = client.put(
            "/api/v1/portfolio/loyalty",
            json={
                "program_name": "skyhigh_airways",
                "program_type": "airline",
                "balance": 10000,
                "status_tier": tier,
            },
            headers=auth(synced_user, jwt_secret),
        )
        assert response.status_code == 200

    accounts = client.get(
        "/api/v1/portfolio/loyalty", headers=auth(synced_user, jwt_secret)
    ).json()["data"]
    assert len(accounts) == 1
    assert accounts[0]["status_tier"] == "Gold"


def test_preferences_put_merges(client, jwt_secret, synced_user):
    """A client sending one field must not erase preferences it never knew of."""
    client.put(
        "/api/v1/preferences",
        json={"values": {"home_airport": "DEL", "redemption_strategy": "maximize"}},
        headers=auth(synced_user, jwt_secret),
    )
    response = client.put(
        "/api/v1/preferences",
        json={"values": {"home_airport": "BOM"}},
        headers=auth(synced_user, jwt_secret),
    )
    values = response.json()["data"]["values"]
    assert values == {"home_airport": "BOM", "redemption_strategy": "maximize"}


def test_goals_create_and_list(client, jwt_secret, synced_user):
    response = client.post(
        "/api/v1/goals",
        json={
            "goal_type": "trip",
            "description": "Award flight to Tokyo",
            "target_date": "2027-03-01",
        },
        headers=auth(synced_user, jwt_secret),
    )
    assert response.status_code == 200
    listed = client.get("/api/v1/goals", headers=auth(synced_user, jwt_secret)).json()["data"]
    assert [g["description"] for g in listed] == ["Award flight to Tokyo"]


def test_invalid_goal_type_is_rejected(client, jwt_secret, synced_user):
    response = client.post(
        "/api/v1/goals",
        json={"goal_type": "vibes", "description": "?"},
        headers=auth(synced_user, jwt_secret),
    )
    assert response.status_code == 422


def test_health_reports_the_database_as_ok_when_connected(client):
    assert client.get("/api/v1/health").json()["data"]["checks"]["database"] == "ok"
