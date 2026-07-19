"""Verified-value structure shared by rules, knowledge seeds, and graph edges.

Every numeric fact in the system carries this structure. `unverified` status
means "cannot compute" — engines refuse to compute with it and
recommendations surface it as unknown. Unknown is always preferred over
incorrect (BUILD_SPEC §3, §5).

Confidence semantics (spec update 2026-07-19, product owner — see ADR-001
amendment): on an unverified value, confidence records the strength of the
unofficial evidence behind the candidate value (always < 1, and never enough
to compute with); on a verified value it must be > 0. Unverified values may
carry a candidate `value` for audit/verification purposes — `is_usable`
still gates all computation on verified status.
"""

from typing import ClassVar, Literal

from pydantic import BaseModel, Field, model_validator


class VerifiedValue(BaseModel):
    value: float | None = None
    status: Literal["verified", "unverified"] = "unverified"
    source: str | None = None
    confidence: float = 0.0

    @model_validator(mode="after")
    def _enforce_integrity(self) -> "VerifiedValue":
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.status == "unverified" and self.confidence >= 1.0:
            raise ValueError("unverified values cannot claim full confidence")
        if self.status == "verified":
            if self.value is None:
                raise ValueError("verified values must carry a value")
            if not self.source:
                raise ValueError("verified values must carry a source")
            if self.confidence <= 0.0:
                raise ValueError("verified values must carry confidence > 0")
        return self

    @property
    def is_usable(self) -> bool:
        """True only when the value may enter deterministic computation."""
        return self.status == "verified" and self.value is not None

    @classmethod
    def unknown(cls) -> "VerifiedValue":
        return cls(value=None, status="unverified", source=None, confidence=0.0)


class PointValueReference(BaseModel):
    """Per-channel point value reference (spec update 2026-07-19): a reward
    point is worth different amounts depending on how it is redeemed."""

    cashback: VerifiedValue = Field(default_factory=VerifiedValue.unknown)
    voucher: VerifiedValue = Field(default_factory=VerifiedValue.unknown)
    travel: VerifiedValue = Field(default_factory=VerifiedValue.unknown)

    CHANNELS: ClassVar[tuple[str, ...]] = ("cashback", "voucher", "travel")

    def for_channel(self, channel: str) -> VerifiedValue:
        if channel not in self.CHANNELS:
            raise ValueError(f"unknown redemption channel '{channel}'")
        return getattr(self, channel)

    @classmethod
    def unknown(cls) -> "PointValueReference":
        return cls()
