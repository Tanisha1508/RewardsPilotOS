"""Query strings must not reach an access log (privacy audit P6, implemented
2026-07-30).

The logging policy was adopted on the basis that this service logs nothing,
which is true of application logging and false of the server beneath it:
uvicorn's `uvicorn.access` logger is on by default and writes the full URL. So
`GET /api/v1/knowledge/search?q=...` has been reaching Render's logs all along.

Tested through the real `logging` machinery rather than by calling `scrub_path`
directly — the helper being correct proves nothing if the filter is never
attached, or is attached to the wrong logger, or stops matching uvicorn's record
shape after an upgrade.
"""

import logging

from backend.main import create_app
from infra.logging.access_log import ScrubAccessLogPaths, install_access_log_scrubber, scrub_path

# The record uvicorn actually emits: format '%s - "%s %s HTTP/%s" %d' with
# (client_addr, method, full_path, http_version, status_code).
ACCESS_FORMAT = '%s - "%s %s HTTP/%s" %d'


def _formatted(path: str) -> str:
    """Push a uvicorn-shaped record through the installed filter and format it,
    returning the line that would actually be written."""
    install_access_log_scrubber()
    logger = logging.getLogger("uvicorn.access")
    record = logger.makeRecord(
        "uvicorn.access",
        logging.INFO,
        __file__,
        0,
        ACCESS_FORMAT,
        ("127.0.0.1:0", "GET", path, "1.1", 200),
        None,
    )
    for log_filter in logger.filters:
        log_filter.filter(record)
    return record.getMessage()


def test_the_search_query_never_reaches_the_line():
    """P6 itself: the endpoint takes user-supplied text in the URL."""
    line = _formatted("/api/v1/knowledge/search?q=how+do+i+transfer+edge+miles")

    assert "how+do+i+transfer" not in line
    assert "q=" not in line
    assert "/api/v1/knowledge/search" in line  # the route still identifies itself


def test_path_identifiers_collapse_to_the_route_template():
    """The policy asks for the route template. The server logs the URL that
    arrived, so ids are populated unless something puts them back."""
    line = _formatted("/api/v1/goals/6f1c2d3e-4a5b-4c6d-8e9f-0a1b2c3d4e5f")

    assert "6f1c2d3e" not in line
    assert "/api/v1/goals/{id}" in line


def test_status_and_method_survive():
    """This suppresses the contents of a line, never the line. Access logs are
    how you find out the service is being scanned."""
    line = _formatted("/api/v1/health")

    assert "GET" in line
    assert "200" in line
    assert "/api/v1/health" in line


def test_creating_the_app_installs_the_filter():
    """The filter is worthless unless something attaches it. `create_app` is the
    single entry point every deployment goes through."""
    logging.getLogger("uvicorn.access").filters = [
        existing
        for existing in logging.getLogger("uvicorn.access").filters
        if not isinstance(existing, ScrubAccessLogPaths)
    ]

    create_app()

    assert any(
        isinstance(existing, ScrubAccessLogPaths)
        for existing in logging.getLogger("uvicorn.access").filters
    )


def test_installation_is_idempotent():
    """`create_app()` runs once in production and many times across a test
    session, and a logger's filter list is process-global."""
    for _ in range(5):
        install_access_log_scrubber()

    attached = [
        existing
        for existing in logging.getLogger("uvicorn.access").filters
        if isinstance(existing, ScrubAccessLogPaths)
    ]
    assert len(attached) == 1


def test_a_record_that_is_not_an_access_line_is_left_alone():
    """Other uvicorn loggers share the process. Rewriting args positionally on a
    record that is not an access line would corrupt an unrelated message."""
    install_access_log_scrubber()
    logger = logging.getLogger("uvicorn.access")
    record = logger.makeRecord(
        "uvicorn.access", logging.INFO, __file__, 0, "startup complete on %s", ("?q=keep",), None
    )
    for log_filter in logger.filters:
        log_filter.filter(record)

    assert record.getMessage() == "startup complete on ?q=keep"


def test_scrub_path_handles_both_at_once():
    assert scrub_path("/api/v1/goals/6f1c2d3e-4a5b-4c6d-8e9f-0a1b2c3d4e5f?q=secret") == (
        "/api/v1/goals/{id}"
    )
