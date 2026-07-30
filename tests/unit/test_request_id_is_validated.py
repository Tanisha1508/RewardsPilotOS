"""A caller-supplied request id must be a UUID or be replaced (privacy P8).

`x-request-id` is echoed back in every response envelope and would reach any log
line the service ever gains. Accepting arbitrary text let a caller inject
newlines, control characters, or another user's identifier into our own records.

Honouring a *valid* supplied id stays: it is what lets a client correlate its
logs with ours.
"""

import uuid

from backend.middleware.request_context import _accepted_request_id


def test_a_valid_uuid_is_honoured():
    supplied = str(uuid.uuid4())
    assert _accepted_request_id(supplied) == supplied


def test_absent_gets_a_fresh_uuid():
    generated = _accepted_request_id(None)
    uuid.UUID(generated)  # raises if not a uuid


def test_injection_shaped_values_are_replaced():
    """Each of these, echoed into a log line or a response header, is a problem
    rather than a label."""
    for hostile in (
        "not-a-uuid",
        "abc\nINFO fake log line",  # log injection
        "abc\r\nSet-Cookie: a=b",  # header injection
        "../../etc/passwd",
        "<script>alert(1)</script>",
        "'; drop table users; --",
        "x" * 5000,  # unbounded length
        "",
    ):
        result = _accepted_request_id(hostile)
        assert result != hostile
        uuid.UUID(result)  # and what we substituted is a real uuid


def test_a_uuid_in_a_different_format_is_normalised():
    """Braced and unbraced forms are the same id; normalising means two log
    lines for one request cannot disagree about its name."""
    plain = uuid.uuid4()
    assert _accepted_request_id(f"{{{plain}}}") == str(plain)
    assert _accepted_request_id(str(plain).upper()) == str(plain)
