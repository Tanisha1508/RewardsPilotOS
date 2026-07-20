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
