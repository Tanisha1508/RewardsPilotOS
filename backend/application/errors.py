"""Domain exceptions raised by the application layer.

BUILD_SPEC §3: services raise domain exceptions, the API layer maps them to
HTTP errors. Services therefore never import `fastapi` — they say what went
wrong, not what status code it deserves, which keeps them usable from the
LangGraph workflow and background jobs as well as from routers.
"""


class ApplicationError(Exception):
    """Base for anything the API layer knows how to translate."""

    code = "application_error"


class NotFoundError(ApplicationError):
    code = "not_found"


class ConflictError(ApplicationError):
    """The request contradicts existing state (duplicate key, stale write)."""

    code = "conflict"


class PermissionDeniedError(ApplicationError):
    """The row exists but belongs to someone else.

    Deliberately distinct from NotFoundError inside the code, and deliberately
    reported as 404 at the boundary: telling a caller "that card exists, just
    not yours" confirms the existence of another user's data.
    """

    code = "not_found"


class InvalidReferenceError(ApplicationError):
    """A field names something that does not exist, or exists as the wrong kind
    of thing (B1 / KNOWN_LIMITATIONS 31).

    Distinct from a schema failure, which the request never gets past: the value
    is a well-formed string, it just does not refer to anything usable. Reported
    as 422 — the request was understood and is wrong, rather than malformed.
    """

    code = "invalid_reference"
