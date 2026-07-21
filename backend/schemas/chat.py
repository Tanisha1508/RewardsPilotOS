"""HTTP DTOs for the chat / recommendations endpoints (BUILD_SPEC §9)."""

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatIn(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class RecommendationOut(BaseModel):
    """A persisted recommendation as returned to the client. `recommendation` is
    the full structured object the workflow produced (decision, reasoning,
    calculations, citations, confidence, assumptions, alternatives) — stored and
    returned as written, never regenerated (BUILD_SPEC §4)."""

    model_config = ConfigDict(from_attributes=True)

    rec_id: uuid.UUID
    query: str
    recommendation: dict
    confidence: str | None
    citations: list = Field(default_factory=list)
    status: str
    created_at: str

    @classmethod
    def from_model(cls, row) -> "RecommendationOut":
        return cls(
            rec_id=row.rec_id,
            query=row.query,
            recommendation=row.recommendation_json,
            confidence=row.confidence,
            citations=row.citations_json or [],
            status=row.status,
            created_at=row.created_at.isoformat(),
        )


class FeedbackIn(BaseModel):
    # BUILD_SPEC §9: accepted | rejected | saved. "viewed" is set by GET, not here.
    status: Literal["accepted", "rejected", "saved"]
