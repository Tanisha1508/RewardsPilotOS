"""VerifiedValue model invariants (contracts/api/verified_value.py)."""

import pytest
from pydantic import ValidationError

from contracts.api.verified_value import VerifiedValue


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


INVALID_TABLE = [
    {"value": 5, "status": "unverified", "source": None, "confidence": 0.5},
    {"value": None, "status": "verified", "source": "https://example.test", "confidence": 0.9},
    {"value": 5, "status": "verified", "source": None, "confidence": 0.9},
    {"value": 5, "status": "verified", "source": "https://example.test", "confidence": 1.7},
    {"value": 5, "status": "verified", "source": "https://example.test", "confidence": -0.1},
]


@pytest.mark.parametrize("payload", INVALID_TABLE)
def test_integrity_violations_rejected(payload):
    with pytest.raises(ValidationError):
        VerifiedValue.model_validate(payload)


def test_unverified_with_rumored_value_is_not_usable():
    rumored = VerifiedValue(value=500, status="unverified", source=None, confidence=0.0)
    assert rumored.is_usable is False
