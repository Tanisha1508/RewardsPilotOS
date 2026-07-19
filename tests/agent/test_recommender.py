"""Recommender: contract validation, verbatim numbers, retry, typed failure."""

from agents.recommendation.recommender import recommend
from agents.state.schema import initial_state
from contracts.tools.knowledge_search import ChunkMetadata, RetrievedChunk
from tests.agent.fakes import BrokenLLM, PayloadLLM, valid_recommendation

RULE_RESULT = {"tool": "CalculateEarn", "card_key": "test", "points": 1500.0}
CHUNK = RetrievedChunk(
    doc_id="doc1",
    chunk_index=0,
    content="text",
    score=0.5,
    metadata=ChunkMetadata(
        doc_id="doc1",
        issuer="demo_bank",
        program="voyager_points",
        doc_type="reward_rules",
        source_url="https://example.test/doc1",
        last_changed="2026-06-15",
    ),
)


def _state():
    state = initial_state("q", "u")
    state["rule_results"] = [RULE_RESULT]
    state["knowledge"] = [CHUNK]
    return state


def test_valid_output_accepted():
    payload = valid_recommendation(
        calculations=[RULE_RESULT],
        citations=[{
            "source_url": "https://example.test/doc1",
            "last_changed": "2026-06-15",
            "doc_id": "doc1",
        }],
    )
    state = recommend(_state(), PayloadLLM(recommender_payloads=[payload]))
    assert state["recommendation"]["decision"] == "test decision"
    assert state["confidence"] == "low"
    assert state["citations"][0].source_url == "https://example.test/doc1"


def test_altered_number_rejected_then_retry_succeeds():
    tampered = valid_recommendation(
        calculations=[{**RULE_RESULT, "points": 9999.0}]  # LLM invented a number
    )
    good = valid_recommendation(calculations=[RULE_RESULT])
    llm = PayloadLLM(recommender_payloads=[tampered, good])
    state = recommend(_state(), llm)
    assert llm.recommender_calls == 2
    assert state["recommendation"]["calculations"] == [RULE_RESULT]


def test_persistent_violation_is_typed_failure():
    tampered = valid_recommendation(calculations=[{"tool": "made_up", "points": 1.0}])
    state = recommend(_state(), PayloadLLM(recommender_payloads=[tampered, tampered]))
    assert state["recommendation"] is None
    assert state["confidence"] == "low"
    assert any("typed failure after retry" in error for error in state["errors"])


def test_uncited_source_rejected():
    payload = valid_recommendation(
        citations=[{
            "source_url": "https://evil.example/fake",
            "last_changed": "2026-01-01",
            "doc_id": None,
        }]
    )
    state = recommend(_state(), PayloadLLM(recommender_payloads=[payload, payload]))
    assert state["recommendation"] is None
    assert any("typed failure" in error for error in state["errors"])


def test_invalid_json_retried_then_failed():
    state = recommend(_state(), PayloadLLM(recommender_payloads=["not json", "still not"]))
    assert state["recommendation"] is None


def test_llm_outage_is_graceful():
    state = recommend(_state(), BrokenLLM())
    assert state["recommendation"] is None
    assert any("recommender:" in error for error in state["errors"])
