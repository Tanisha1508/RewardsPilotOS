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
    # Set when the currency is not a node in the transfer graph at all, which is
    # missing data rather than an absence of partners (spec update 2026-07-20;
    # see BestTransferPathsOutput.no_transfer_data for the full reasoning).
    no_transfer_data: str | None = None

    @property
    def is_unresolved_input(self) -> bool:
        """True when the tool ran correctly but could not resolve its input —
        the currency is not in the graph, so there is no answer to give, only a
        data gap to report. The Tool Registry lifts this to a distinct
        `unresolved_input` status so the caller never has to infer it from an
        empty `ratios` list (KNOWN_LIMITATIONS 24, Class B)."""
        return self.no_transfer_data is not None and not self.ratios
