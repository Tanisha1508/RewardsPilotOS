"""Opportunity Engine tool contract: GetOpportunities (BUILD_SPEC §8).

Sprint returns fixture notifications; D5 wires monitor.py change records."""

from pydantic import BaseModel, Field


class GetOpportunitiesInput(BaseModel):
    # No user_id — resolved from the ambient `acting_as` context
    # (KNOWN_LIMITATIONS 24, Class C).
    limit: int = Field(default=10, ge=1, le=50)


class Opportunity(BaseModel):
    notif_id: str
    type: str  # promotion | expiry | rule_change | unused_benefit
    title: str
    body: str
    source_change_id: str | None = None
    source_url: str | None = None
    created_at: str


class GetOpportunitiesOutput(BaseModel):
    opportunities: list[Opportunity] = Field(default_factory=list)
