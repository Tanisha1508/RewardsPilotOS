"""Memory tool contracts: RecallMemory, StorePreference (BUILD_SPEC §8).

Retrieval only — nothing is appended blindly to prompts. The Planner requests
memory recall only when the intent benefits."""

from pydantic import BaseModel, Field


class RecallMemoryInput(BaseModel):
    # No user_id: the caller's identity is resolved from the ambient
    # `acting_as` context, never from model output (KNOWN_LIMITATIONS 24,
    # Class C). See `contracts/tools/portfolio.UserScopedInput`.
    intent: str
    query: str
    limit: int = Field(default=5, ge=1, le=20)


class EpisodicEvent(BaseModel):
    event_id: str
    event_type: str
    payload: dict = Field(default_factory=dict)
    created_at: str


class RecallMemoryOutput(BaseModel):
    preferences: dict[str, str] = Field(default_factory=dict)
    episodic: list[EpisodicEvent] = Field(default_factory=list)


class StorePreferenceInput(BaseModel):
    # No user_id — see RecallMemoryInput above. Writing to the wrong user's
    # preferences on a hallucinated id would be worse than reading.
    key: str
    value: str


class StorePreferenceOutput(BaseModel):
    stored: bool
    key: str
    value: str
