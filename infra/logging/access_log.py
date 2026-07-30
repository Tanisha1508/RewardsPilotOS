"""Enforce `docs/LOGGING_POLICY.md` on the one logger we do not write
(privacy audit P6, implemented 2026-07-30).

The policy was adopted on the basis that this service logs nothing. That is true
of *application* logging — there is no `logger` call in `backend/`, `agents/`,
`tools/`, `rules/` or `graph/` — and false of the server underneath it. Uvicorn
installs a `uvicorn.access` logger that is on by default and writes:

    127.0.0.1:0 - "GET /api/v1/knowledge/search?q=edge+miles HTTP/1.1" 200

Query string included. Render captures stdout. So P6's exposure was not latent
after all: `?q=` has been reaching a log the whole time, written by a logger
nobody in this repo configured.

Installed in `create_app()` rather than passed to `uvicorn` on the command line
because the start command lives in Render's dashboard, not in this repository.
A defence that depends on a flag in a web console someone else can edit is not a
defence — this holds however the app is started, including under a different
server, and travels with the code.

A filter rather than a custom formatter: filters run before formatting and can
rewrite `record.args`, so the scrub applies whatever log format is configured.
"""

import logging
import re

# Uvicorn's access record carries args (client_addr, method, full_path,
# http_version, status_code) against the format '%s - "%s %s HTTP/%s" %d'.
_ACCESS_ARG_COUNT = 5
_PATH_INDEX = 2

_QUERY_STRING = re.compile(r"\?.*$")

# Path parameters are populated in an access line — `/goals/<uuid>`, never
# `/goals/{goal_id}` — because the server logs the URL, not the route that
# matched it. Collapsing them restores the route template the policy asks for.
# The UUID form is unambiguous, so this cannot swallow a meaningful path
# segment.
_UUID_SEGMENT = re.compile(
    r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def scrub_path(path: str) -> str:
    """Reduce a populated request URL to its route template.

    `/api/v1/knowledge/search?q=how+do+i+transfer` -> `/api/v1/knowledge/search`
    `/api/v1/goals/6f1c...-...` -> `/api/v1/goals/{id}`
    """
    return _UUID_SEGMENT.sub("/{id}", _QUERY_STRING.sub("", path))


class ScrubAccessLogPaths(logging.Filter):
    """Rewrites the path in a uvicorn access record, in place, before it is
    formatted.

    Always returns True: this suppresses the *contents* of a line, never the
    line. Access logs are how you find out the service is being hammered or
    scanned, and dropping them to protect a query string would trade one
    operational property for another.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if not isinstance(args, tuple) or len(args) != _ACCESS_ARG_COUNT:
            return True
        path = args[_PATH_INDEX]
        if isinstance(path, str) and ("?" in path or "-" in path):
            record.args = args[:_PATH_INDEX] + (scrub_path(path),) + args[_PATH_INDEX + 1 :]
        return True


def install_access_log_scrubber() -> None:
    """Attach the filter to `uvicorn.access`. Idempotent.

    `create_app()` runs once per process in production but many times across a
    test session, and a logger's filter list is process-global — without the
    guard the filter would stack up and run once per call.
    """
    access_logger = logging.getLogger("uvicorn.access")
    if any(isinstance(existing, ScrubAccessLogPaths) for existing in access_logger.filters):
        return
    access_logger.addFilter(ScrubAccessLogPaths())
