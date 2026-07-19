"""Recommendation JSON contract (BUILD_SPEC §8). The LLM never invents output
formats; Recommender output is validated against this model before
persistence. `calculations` entries are copied verbatim from rule_results and
graph_results — validation enforces it."""

from typing import Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    source_url: str
    last_changed: str
    doc_id: str | None = None


class Confidence(BaseModel):
    level: Literal["high", "medium", "low"]
    reason: str


class Recommendation(BaseModel):
    decision: str
    reasoning: list[str] = Field(default_factory=list)
    calculations: list[dict] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    confidence: Confidence
    assumptions: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)


class RecommendationValidationError(Exception):
    """Recommender output violates the contract (schema, non-verbatim
    calculations, or uncited sources)."""


def validate_recommendation(
    payload: dict,
    rule_results: list[dict],
    graph_results: list[dict],
    retrieved_sources: list[Citation],
) -> Recommendation:
    """Validate schema + data integrity:
    - every calculations entry must be verbatim (deep-equal) from
      rule_results or graph_results — the LLM never does arithmetic
    - every citation must come from actually retrieved sources
    """
    recommendation = Recommendation.model_validate(payload)
    allowed = list(rule_results) + list(graph_results)
    for entry in recommendation.calculations:
        if entry not in allowed:
            raise RecommendationValidationError(
                f"calculation entry not verbatim from tool results: {entry}"
            )
    allowed_sources = {(c.source_url, c.last_changed) for c in retrieved_sources}
    for citation in recommendation.citations:
        if (citation.source_url, citation.last_changed) not in allowed_sources:
            raise RecommendationValidationError(
                f"citation not backed by retrieved sources: {citation.source_url}"
            )
    return recommendation
