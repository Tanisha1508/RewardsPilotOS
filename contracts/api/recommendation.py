"""Recommendation JSON contract (BUILD_SPEC §8). The LLM never invents output
formats; Recommender output is validated against this model before
persistence. `calculations` entries are copied verbatim from rule_results and
graph_results — validation enforces it."""

import re
from typing import Literal

from pydantic import BaseModel, Field

# Numbers in prose that could carry reward math: two or more digits
# (optionally comma-grouped), OR any decimal. Decimals matter even when short —
# "worth 2.5 rupees a point" is a valuation. Bare single digits ("3 cards")
# are conversational and deliberately not matched.
_PROSE_NUMBER_RE = re.compile(r"\d[\d,]+(?:\.\d+)?|\d+\.\d+")

# Confidence ordering, defined alongside the Literal it ranks.
LEVEL_RANK = {"low": 0, "medium": 1, "high": 2}


def exceeds_ceiling(level: str, ceiling: str) -> bool:
    """True when `level` claims more confidence than `ceiling` allows.
    Reporting lower than the ceiling is always permitted."""
    return LEVEL_RANK[level] > LEVEL_RANK[ceiling]


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
    grounded_text: str | None = None,
    confidence_ceiling: str | None = None,
    required_statement: str | list[str] | None = None,
) -> Recommendation:
    """Validate schema + data integrity:
    - every calculations entry must be verbatim (deep-equal) from
      rule_results or graph_results — the LLM never does arithmetic
    - every citation must come from actually retrieved sources
    - when `grounded_text` is given (tool results + retrieved knowledge,
      NOT the user query), every 2+ digit number in the prose fields must
      appear in it — an LLM cannot smuggle arithmetic or user-supplied
      figures through `decision`/`reasoning`
    - when `confidence_ceiling` is given, the reported confidence may not
      exceed what the evidence supports (agents.recommendation.calibration)
    - when `required_statement` is given (one string or several), each must
      appear VERBATIM in the decision or reasoning. Used for deterministic
      sentences that must reach the user intact rather than being softened or
      dropped: the winning-margin caveat (agents.recommendation.margin), which
      names which specific number carries a comparison, and lapsed-rate expiry
      notes (ADR-012), which say a card's accelerated rate has expired and the
      figure shown is base earn. A prompt instruction is not a guarantee;
      anything that must reach the user is checked here.
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
    if confidence_ceiling is not None and exceeds_ceiling(
        recommendation.confidence.level, confidence_ceiling
    ):
        raise RecommendationValidationError(
            f"confidence '{recommendation.confidence.level}' exceeds what the "
            f"evidence supports (ceiling '{confidence_ceiling}')"
        )
    required = (
        [required_statement]
        if isinstance(required_statement, str)
        else list(required_statement or [])
    )
    for statement in required:
        if not any(
            statement in field for field in [recommendation.decision, *recommendation.reasoning]
        ):
            raise RecommendationValidationError(
                f"required statement missing from decision/reasoning — it must "
                f"appear verbatim, not paraphrased or folded into the confidence "
                f"reason: {statement!r}"
            )
    if grounded_text is not None:
        prose = " ".join(
            [recommendation.decision, recommendation.confidence.reason]
            + recommendation.reasoning
            + recommendation.assumptions
            + recommendation.alternatives
        )
        stripped_allowed = grounded_text.replace(",", "")
        for token in _PROSE_NUMBER_RE.findall(prose):
            if token in grounded_text or token.replace(",", "") in stripped_allowed:
                continue
            raise RecommendationValidationError(
                f"number in prose not traceable to tool results or retrieved " f"knowledge: {token}"
            )
    return recommendation
