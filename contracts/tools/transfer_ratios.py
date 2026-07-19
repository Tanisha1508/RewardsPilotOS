"""GetTransferRatios tool contract (BUILD_SPEC §8): verified outbound
transfer edges for a reward currency; unverified partners surfaced as notes."""

from pydantic import BaseModel, Field

from contracts.api.verified_value import VerifiedValue


class GetTransferRatiosInput(BaseModel):
    currency: str


class TransferRatio(BaseModel):
    from_currency: str
    to_program: str
    ratio: VerifiedValue
    min_transfer: VerifiedValue
    last_verified: str | None = None
    source_doc_id: str | None = None


class GetTransferRatiosOutput(BaseModel):
    currency: str
    ratios: list[TransferRatio] = Field(default_factory=list)
    unverified_partners: list[str] = Field(default_factory=list)
