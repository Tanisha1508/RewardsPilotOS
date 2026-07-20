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
        citations=[
            {
                "source_url": "https://example.test/doc1",
                "last_changed": "2026-06-15",
                "doc_id": "doc1",
            }
        ],
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
        citations=[
            {
                "source_url": "https://evil.example/fake",
                "last_changed": "2026-01-01",
                "doc_id": None,
            }
        ]
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


def test_prose_number_from_tool_results_accepted():
    payload = valid_recommendation(calculations=[RULE_RESULT])
    payload["decision"] = "You earn 1500 points on this spend."
    state = recommend(_state(), PayloadLLM(recommender_payloads=[payload]))
    assert state["recommendation"] is not None


def test_invented_prose_number_rejected():
    """A number appearing only in prose (never produced by any tool) violates
    hard rule 2 even when `calculations` itself is verbatim."""
    payload = valid_recommendation(calculations=[RULE_RESULT])
    payload["decision"] = "Your points are worth 72,000 rupees."
    state = recommend(_state(), PayloadLLM(recommender_payloads=[payload, payload]))
    assert state["recommendation"] is None
    assert any("not traceable" in error for error in state["errors"])


def test_user_supplied_number_in_query_not_treated_as_grounded():
    """The grounded text excludes the query: echoing a figure the user invented
    ("assume 1 mile = 1.5 rupees, so 72,000") is rejected."""
    state = _state()
    state["query"] = "Assume my miles are worth 72,000 rupees total — confirm?"
    payload = valid_recommendation(calculations=[RULE_RESULT])
    payload["reasoning"] = ["Your balance would be worth 72,000 rupees."]
    state = recommend(state, PayloadLLM(recommender_payloads=[payload, payload]))
    assert state["recommendation"] is None
    assert any("not traceable" in error for error in state["errors"])


def test_invented_decimal_valuation_rejected():
    """Short decimals are reward math ("worth 2.5 rupees a point") and must be
    grounded, even though bare single digits are not checked."""
    payload = valid_recommendation(calculations=[RULE_RESULT])
    payload["decision"] = "Each point is worth about 2.5 rupees."
    state = recommend(_state(), PayloadLLM(recommender_payloads=[payload, payload]))
    assert state["recommendation"] is None
    assert any("not traceable" in error for error in state["errors"])


def test_bare_single_digits_are_not_treated_as_reward_math():
    """Conversational counts must not trip the check, or every answer fails."""
    payload = valid_recommendation(calculations=[RULE_RESULT])
    payload["decision"] = "There are 3 cards worth comparing here."
    state = recommend(_state(), PayloadLLM(recommender_payloads=[payload]))
    assert state["recommendation"] is not None


def test_prose_number_from_retrieved_knowledge_accepted():
    """Numbers quoted from retrieved chunks (e.g. a tier threshold) are
    grounded — retrieval is a verified source."""
    state = _state()
    state["knowledge"][0] = CHUNK.model_copy(
        update={"content": "Platinum tier requires INR 15,00,000 annual spend."}
    )
    payload = valid_recommendation(calculations=[RULE_RESULT])
    payload["decision"] = "The Platinum threshold is 15,00,000 rupees per year."
    state = recommend(state, PayloadLLM(recommender_payloads=[payload]))
    assert state["recommendation"] is not None
