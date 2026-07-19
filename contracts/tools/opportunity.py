"""Opportunity Engine tool contract: GetOpportunities (BUILD_SPEC §8).

Sprint returns fixture notifications; D5 wires monitor.py change records."""

from pydantic import BaseModel, Field


class GetOpportunitiesInput(BaseModel):
    user_id: str
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
