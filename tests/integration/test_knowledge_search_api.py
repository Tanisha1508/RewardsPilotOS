"""GET /api/v1/knowledge/search against a real retriever (D3, BUILD_SPEC §9).

Uses a ChromaDB persist dir seeded from the real seed corpus, so the endpoint
is exercised against actual embeddings and the real hybrid ranking — not a
stub. The retriever singleton is redirected at that dir for the test.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from tests.unit.test_auth_tokens import make_token


@pytest.fixture(scope="module")
def seeded_persist_dir(tmp_path_factory):
    """Ingest the real seed corpus into a temp ChromaDB once for this module."""
    from knowledge.pipeline.ingest import ingest_sources
    from knowledge.storage.collections import get_client

    persist = tmp_path_factory.mktemp("knowledge_api_chroma")
    ingest_sources(get_client(persist))
    return str(persist)


@pytest.fixture()
def client(jwt_secret, seeded_persist_dir, monkeypatch):
    # Point the cached retriever singleton at the seeded corpus.
    from tools.knowledge_search import service

    service.get_retriever.cache_clear()
    monkeypatch.setattr(
        service, "get_retriever", lambda persist_dir=None: _retriever(seeded_persist_dir)
    )
    with TestClient(create_app(), raise_server_exceptions=False) as test_client:
        yield test_client


def _retriever(persist_dir):
    from knowledge.retrieval.hybrid import HybridRetriever
    from knowledge.storage.collections import get_client

    return HybridRetriever(get_client(persist_dir))


def auth(secret):
    return {"Authorization": f"Bearer {make_token(secret, sub=uuid.uuid4())}"}


def test_search_requires_authentication(client):
    assert client.get("/api/v1/knowledge/search?q=infinia").status_code == 401


def test_search_returns_cited_chunks(client, jwt_secret):
    r = client.get(
        "/api/v1/knowledge/search",
        params={"q": "HDFC Infinia SmartBuy accelerated earning", "issuer": "hdfc"},
        headers=auth(jwt_secret),
    )
    assert r.status_code == 200
    chunks = r.json()["data"]["chunks"]
    assert chunks, "expected at least one chunk for a corpus term"
    top = chunks[0]
    # The metadata that becomes a citation must be present and verbatim.
    assert top["metadata"]["issuer"] == "hdfc"
    assert top["metadata"]["source_url"].startswith("http")
    assert top["metadata"]["last_changed"]


def test_empty_query_is_a_422_not_an_empty_result(client, jwt_secret):
    """An empty query is a client error, not "nothing matched" — the two must
    not look the same."""
    assert client.get("/api/v1/knowledge/search?q=", headers=auth(jwt_secret)).status_code == 422


def test_doc_type_filter_scopes_the_collection(client, jwt_secret):
    r = client.get(
        "/api/v1/knowledge/search",
        params={"q": "transfer partners", "doc_type": "transfer_rules"},
        headers=auth(jwt_secret),
    )
    assert r.status_code == 200
    for chunk in r.json()["data"]["chunks"]:
        assert chunk["metadata"]["doc_type"] == "transfer_rules"


def test_response_uses_the_standard_envelope(client, jwt_secret):
    body = client.get("/api/v1/knowledge/search?q=lounge", headers=auth(jwt_secret)).json()
    assert set(body) == {"data", "error", "meta"}
    assert body["error"] is None
    assert body["meta"]["request_id"]
