"""Envelope helpers and domain-exception mapping for routers.

BUILD_SPEC §3 gives one envelope for every response. Routers therefore return
`ok(...)` rather than raw models, and raise domain exceptions rather than
`HTTPException` — the mapping from exception to status code lives here, in one
place, so the same service is reusable outside HTTP (BUILD_SPEC §3: no
business logic in routers).
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from backend.application.errors import (
    ApplicationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
)
from backend.auth.tokens import AuthError, AuthNotConfiguredError
from contracts.api.envelope import failure, success
from database.postgres.session import DatabaseNotConfiguredError

STATUS_BY_EXCEPTION: list[tuple[type[Exception], int]] = [
    # PermissionDenied before NotFound: it is a subclass-free sibling, but the
    # order documents the intent — an unowned row reports as 404, never 403.
    (PermissionDeniedError, 404),
    (NotFoundError, 404),
    (ConflictError, 409),
    (AuthError, 401),
    (AuthNotConfiguredError, 503),
    (DatabaseNotConfiguredError, 503),
]


def request_id_of(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def ok(request: Request, data) -> JSONResponse:
    payload = data
    if hasattr(data, "model_dump"):
        payload = data.model_dump(mode="json")
    elif isinstance(data, list):
        payload = [d.model_dump(mode="json") if hasattr(d, "model_dump") else d for d in data]
    return JSONResponse(content=success(payload, request_id_of(request)))


def error_response(request: Request, exc: Exception) -> JSONResponse:
    for exc_type, status in STATUS_BY_EXCEPTION:
        if isinstance(exc, exc_type):
            code = getattr(exc, "code", exc_type.__name__)
            return JSONResponse(
                status_code=status,
                content=failure(code, str(exc), request_id_of(request)),
            )
    # Unmapped: report a generic message rather than the exception text, which
    # can carry SQL, file paths, or connection strings.
    return JSONResponse(
        status_code=500,
        content=failure("internal_error", "internal server error", request_id_of(request)),
    )


HANDLED_EXCEPTIONS = (
    ApplicationError,
    AuthError,
    AuthNotConfiguredError,
    DatabaseNotConfiguredError,
)
