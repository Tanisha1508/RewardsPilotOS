"""POST /api/v1/chat and the recommendations lifecycle against real Postgres.

The workflow's LLM is scripted (no network, deterministic) — the point here is
the *wiring*: acting_as, persistence, the empty-portfolio path reaching the
endpoint, ownership isolation, and the feedback state machine. The reasoning
quality is the agent suite's job; this is the HTTP + DB seam.
"""

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from tests.unit.test_auth_tokens import make_token


class ScriptedLLM:
    """Planner returns a card-dependent intent with no plan; recommender returns
    a minimal contract-valid recommendation (empty calculations/citations are
    always valid). Deterministic, no tools required."""

    def complete(self, system: str, user: str) -> str:
        if "Planner prompt" in system:
            return json.dumps({"intent": "portfolio", "plan": []})
        return json.dumps(
            {
                "decision": "Your HDFC Infinia is your strongest everyday card.",
                "reasoning": ["Based on the cards on file."],
                "calculations": [],
                "citations": [],
                "confidence": {"level": "low", "reason": "illustrative scripted response"},
                "assumptions": [],
                "alternatives": [],
            }
        )


@pytest.fixture()
def client(jwt_secret, monkeypatch):
    # Inject the scripted LLM so /chat runs the real workflow without Gemini.
    from backend.application import chat as chat_module

    monkeypatch.setattr(chat_module, "default_llm", lambda: ScriptedLLM())
    with TestClient(create_app(), raise_server_exceptions=False) as test_client:
        yield test_client


def auth(user_id, secret):
    return {"Authorization": f"Bearer {make_token(secret, sub=user_id)}"}


@pytest.fixture()
def synced(client, jwt_secret, user_id):
    client.post("/api/v1/auth/sync", json={}, headers=auth(user_id, jwt_secret))
    return user_id


def add_card(client, secret, user_id):
    client.post(
        "/api/v1/portfolio/cards",
        json={
            "issuer": "hdfc",
            "card_name": "HDFC Infinia",
            "network": "visa",
            "reward_currency": "hdfc_reward_points",
        },
        headers=auth(user_id, secret),
    )


def test_chat_with_no_cards_returns_add_a_card(client, jwt_secret, synced):
    """The empty-portfolio path, end to end through the endpoint: a synced user
    with zero cards gets the deterministic 'add a card' answer, persisted."""
    r = client.post(
        "/api/v1/chat",
        json={"query": "What's my best card for dining?"},
        headers=auth(synced, jwt_secret),
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert "add a card" in data["recommendation"]["decision"].lower()
    assert data["status"] == "generated"
    assert data["rec_id"]


def test_chat_with_a_card_persists_a_recommendation(client, jwt_secret, synced):
    add_card(client, jwt_secret, synced)
    r = client.post(
        "/api/v1/chat",
        json={"query": "Which of my cards is best?"},
        headers=auth(synced, jwt_secret),
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    # The gate did NOT fire (user has a card): the scripted recommender answered.
    assert "add a card" not in data["recommendation"]["decision"].lower()
    assert data["recommendation"]["decision"]


def test_recommendation_appears_in_history(client, jwt_secret, synced):
    client.post("/api/v1/chat", json={"query": "q1"}, headers=auth(synced, jwt_secret))
    listed = client.get("/api/v1/recommendations", headers=auth(synced, jwt_secret))
    assert listed.status_code == 200
    assert len(listed.json()["data"]) == 1


def test_get_marks_viewed_then_feedback_sets_status(client, jwt_secret, synced):
    rec_id = client.post(
        "/api/v1/chat", json={"query": "q"}, headers=auth(synced, jwt_secret)
    ).json()["data"]["rec_id"]

    got = client.get(f"/api/v1/recommendations/{rec_id}", headers=auth(synced, jwt_secret))
    assert got.json()["data"]["status"] == "viewed"

    fed = client.post(
        f"/api/v1/recommendations/{rec_id}/feedback",
        json={"status": "accepted"},
        headers=auth(synced, jwt_secret),
    )
    assert fed.json()["data"]["status"] == "accepted"


def test_feedback_rejects_an_invalid_status(client, jwt_secret, synced):
    rec_id = client.post(
        "/api/v1/chat", json={"query": "q"}, headers=auth(synced, jwt_secret)
    ).json()["data"]["rec_id"]
    r = client.post(
        f"/api/v1/recommendations/{rec_id}/feedback",
        json={"status": "loved-it"},
        headers=auth(synced, jwt_secret),
    )
    assert r.status_code == 422


def test_another_users_recommendation_is_not_reachable(client, jwt_secret, synced, user_id):
    rec_id = client.post(
        "/api/v1/chat", json={"query": "q"}, headers=auth(synced, jwt_secret)
    ).json()["data"]["rec_id"]

    intruder = uuid.uuid4()
    client.post("/api/v1/auth/sync", json={}, headers=auth(intruder, jwt_secret))
    # Reported as 404, never 403 — do not confirm the row exists.
    got = client.get(f"/api/v1/recommendations/{rec_id}", headers=auth(intruder, jwt_secret))
    assert got.status_code == 404
    assert client.get(
        "/api/v1/recommendations", headers=auth(intruder, jwt_secret)
    ).json()["data"] == []


def test_empty_query_is_rejected(client, jwt_secret, synced):
    r = client.post("/api/v1/chat", json={"query": ""}, headers=auth(synced, jwt_secret))
    assert r.status_code == 422
