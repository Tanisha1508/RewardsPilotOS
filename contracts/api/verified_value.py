"""Verified-value structure shared by rules, knowledge seeds, and graph edges.

Every numeric fact in the system carries this structure. `null` values and
`unverified` status mean "cannot compute" — engines refuse to compute with
them and recommendations surface them as unknown. Unknown is always preferred
over incorrect (BUILD_SPEC §3, §5).
"""

from typing import Literal

from pydantic import BaseModel, model_validator


class VerifiedValue(BaseModel):
    value: float | None = None
    status: Literal["verified", "unverified"] = "unverified"
    source: str | None = None
    confidence: float = 0.0

    @model_validator(mode="after")
    def _enforce_integrity(self) -> "VerifiedValue":
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.status == "unverified" and self.confidence != 0.0:
            raise ValueError("unverified values must have confidence 0")
        if self.status == "verified":
            if self.value is None:
                raise ValueError("verified values must carry a value")
            if not self.source:
                raise ValueError("verified values must carry a source")
        return self

    @property
    def is_usable(self) -> bool:
        """True only when the value may enter deterministic computation."""
        return self.status == "verified" and self.value is not None

    @classmethod
    def unknown(cls) -> "VerifiedValue":
        return cls(value=None, status="unverified", source=None, confidence=0.0)
