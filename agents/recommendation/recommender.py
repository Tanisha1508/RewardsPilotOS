"""Recommender node (BUILD_SPEC §8): Gemini call that writes the final
recommendation in the exact JSON contract from contracts/api/recommendation.

Validation enforces the hard rules: calculations verbatim from rule_results /
graph_results, citations only from retrieved chunks. Invalid output triggers
the single retry, then a typed failure."""

import json
from pathlib import Path

from agents.recommendation.calibration import confidence_basis
from agents.recommendation.margin import margin_caveat
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


def _state_digest(state: AgentState, basis: dict, caveat: dict | None) -> str:
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
            # Deterministic calibration ceiling: reporting a HIGHER confidence
            # than this is rejected; reporting lower is allowed.
            "confidence_basis": basis,
            # When present, `statement` MUST be reproduced verbatim in the
            # decision or reasoning — validation rejects output without it.
            "margin_caveat": caveat,
        },
        default=str,
    )


def _grounded_text(state: AgentState, caveat: dict | None = None) -> str:
    """Text the prose-number check validates against: everything the tools
    produced or retrieval returned — deliberately excluding the user query, so
    a number the user invented ("assume miles are worth 1.5 rupees") can never
    be echoed back as if it were computed.

    The margin caveat is included because it is deterministic text derived
    from the tool results; its figures are engine outputs, not model claims."""

    def chunk_dump(chunk):
        return chunk.model_dump() if hasattr(chunk, "model_dump") else chunk

    return json.dumps(
        {
            "portfolio": state["portfolio"],
            "preferences": state["preferences"],
            "knowledge": [chunk_dump(c) for c in state["knowledge"]],
            "rule_results": state["rule_results"],
            "graph_results": state["graph_results"],
            "memory": state["memory"],
            "margin_caveat": caveat,
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
    basis = confidence_basis(state["rule_results"], state["graph_results"], state["errors"])
    caveat = margin_caveat(state["rule_results"])
    user = _state_digest(state, basis, caveat)
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
                payload,
                state["rule_results"],
                state["graph_results"],
                retrieved,
                grounded_text=_grounded_text(state, caveat),
                confidence_ceiling=basis["ceiling"],
                required_statement=caveat["statement"] if caveat else None,
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
