"""Recommender node (BUILD_SPEC §8): Gemini call that writes the final
recommendation in the exact JSON contract from contracts/api/recommendation.

Validation enforces the hard rules: calculations verbatim from rule_results /
graph_results, citations only from retrieved chunks. Invalid output triggers
the single retry, then a typed failure."""

import json
from pathlib import Path

from agents.registry import LLM, LLMUnavailableError, complete_with_retry
from agents.state.schema import AgentState
from contracts.api.recommendation import (
    Citation,
    RecommendationValidationError,
    validate_recommendation,
)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "recommender.md"


class RecommendationFailed(Exception):
    """Typed failure after the single retry (BUILD_SPEC §8)."""


def _retrieved_citations(state: AgentState) -> list[Citation]:
    citations = []
    for chunk in state["knowledge"]:
        metadata = chunk.metadata if hasattr(chunk, "metadata") else None
        if metadata is None and isinstance(chunk, dict):
            metadata = chunk.get("metadata")
        if metadata is None:
            continue
        if isinstance(metadata, dict):
            citations.append(
                Citation(
                    source_url=metadata["source_url"],
                    last_changed=metadata["last_changed"],
                    doc_id=metadata.get("doc_id"),
                )
            )
        else:
            citations.append(
                Citation(
                    source_url=metadata.source_url,
                    last_changed=metadata.last_changed,
                    doc_id=metadata.doc_id,
                )
            )
    return citations


def _state_digest(state: AgentState) -> str:
    def chunk_dump(chunk):
        return chunk.model_dump() if hasattr(chunk, "model_dump") else chunk

    return json.dumps(
        {
            "query": state["query"],
            "intent": state["intent"],
            "portfolio": state["portfolio"],
            "preferences": state["preferences"],
            "knowledge": [chunk_dump(c) for c in state["knowledge"]],
            "rule_results": state["rule_results"],
            "graph_results": state["graph_results"],
            "memory": state["memory"],
            "tool_errors": state["errors"],
        },
        default=str,
    )


def _parse_payload(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def recommend(state: AgentState, llm: LLM) -> AgentState:
    system = PROMPT_PATH.read_text()
    user = _state_digest(state)
    retrieved = _retrieved_citations(state)
    feedback = ""
    for attempt in range(2):  # initial + single retry on contract violation
        try:
            raw = complete_with_retry(llm, system, user + feedback)
        except LLMUnavailableError as exc:
            state["errors"].append(f"recommender: {exc}")
            state["recommendation"] = None
            state["confidence"] = "low"
            return state
        try:
            payload = _parse_payload(raw)
            recommendation = validate_recommendation(
                payload, state["rule_results"], state["graph_results"], retrieved
            )
        except (json.JSONDecodeError, RecommendationValidationError, ValueError) as exc:
            feedback = (
                f"\n\nYour previous output was rejected: {exc}. "
                "Follow the contract exactly; copy calculations verbatim."
            )
            if attempt == 1:
                state["errors"].append(f"recommender: typed failure after retry: {exc}")
                state["recommendation"] = None
                state["confidence"] = "low"
                return state
            continue
        state["recommendation"] = recommendation.model_dump()
        state["citations"] = recommendation.citations
        state["confidence"] = recommendation.confidence.level
        return state
    return state  # pragma: no cover - loop always returns
