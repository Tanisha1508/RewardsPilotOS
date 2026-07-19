"""VerifiedValue + PointValueReference invariants (contracts/api).

Confidence semantics per the 2026-07-19 spec update (ADR-001 amendment):
unverified values may carry a candidate value and evidence confidence < 1;
verified values require value + source + confidence > 0. Computation gating
(is_usable) requires verified status regardless of confidence.
"""

import pytest
from pydantic import ValidationError

from contracts.api.verified_value import PointValueReference, VerifiedValue


def test_unknown_factory():
    unknown = VerifiedValue.unknown()
    assert unknown.value is None
    assert unknown.status == "unverified"
    assert unknown.confidence == 0.0
    assert unknown.is_usable is False


def test_verified_usable():
    value = VerifiedValue(
        value=5, status="verified", source="https://example.test/terms", confidence=0.9
    )
    assert value.is_usable is True


def test_unverified_candidate_value_with_evidence_confidence_is_valid_but_unusable():
    candidate = VerifiedValue(
        value=0.3, status="unverified", source="third-party aggregator", confidence=0.5
    )
    assert candidate.is_usable is False


INVALID_TABLE = [
    # unverified cannot claim full confidence
    {"value": 1.0, "status": "unverified", "source": "aggregator", "confidence": 1.0},
    # verified requires a value
    {"value": None, "status": "verified", "source": "https://example.test", "confidence": 0.9},
    # verified requires a source
    {"value": 5, "status": "verified", "source": None, "confidence": 0.9},
    # verified requires confidence > 0
    {"value": 5, "status": "verified", "source": "https://example.test", "confidence": 0.0},
    # confidence bounds
    {"value": 5, "status": "verified", "source": "https://example.test", "confidence": 1.7},
    {"value": 5, "status": "verified", "source": "https://example.test", "confidence": -0.1},
]


@pytest.mark.parametrize("payload", INVALID_TABLE)
def test_integrity_violations_rejected(payload):
    with pytest.raises(ValidationError):
        VerifiedValue.model_validate(payload)


def test_point_value_reference_channels():
    reference = PointValueReference(
        travel=VerifiedValue(
            value=0.5, status="verified", source="https://example.test", confidence=0.9
        )
    )
    assert reference.for_channel("travel").is_usable is True
    assert reference.for_channel("cashback").is_usable is False
    with pytest.raises(ValueError, match="unknown redemption channel"):
        reference.for_channel("crypto")


def test_point_value_reference_unknown_factory():
    reference = PointValueReference.unknown()
    assert all(
        not reference.for_channel(channel).is_usable
        for channel in PointValueReference.CHANNELS
    )


def test_point_value_channel_confirmed_no_single_value():
    """None on a channel = confirmed no single figure exists (tier- or
    partner-dependent) — distinct from the default unknown state."""
    reference = PointValueReference(
        cashback=VerifiedValue(
            value=0.25, status="verified", source="https://example.test", confidence=0.75
        ),
        voucher=None,
        travel=None,
    )
    assert reference.for_channel("cashback").is_usable is True
    assert reference.for_channel("voucher") is None
    assert reference.for_channel("travel") is None
