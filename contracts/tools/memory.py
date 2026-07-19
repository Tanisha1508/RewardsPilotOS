"""Memory tool contracts: RecallMemory, StorePreference (BUILD_SPEC §8).

Retrieval only — nothing is appended blindly to prompts. The Planner requests
memory recall only when the intent benefits."""

from pydantic import BaseModel, Field


class RecallMemoryInput(BaseModel):
    user_id: str
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
    user_id: str
    key: str
    value: str


class StorePreferenceOutput(BaseModel):
    stored: bool
    key: str
    value: str
