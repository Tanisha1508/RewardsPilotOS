"""Per-request identity and database session.

Two jobs, both about giving a request one consistent context:

**Request id.** Generated once, echoed in every envelope's `meta.request_id`,
and reused in error responses so a user-reported failure can be found in logs.

**Session binding.** One session per request, bound as the ambient session
(`database.postgres.session`) so services and tools share a single transaction.
It commits on a successful response and rolls back on an exception, which is
what makes a multi-write endpoint all-or-nothing rather than half-applied.

The session is opened lazily: most of the cost of a request that never touches
the database is the connection, and `/health` and 404s should not pay it.
"""

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from database.postgres.session import DatabaseNotConfiguredError, bind_session, new_session

_request_id: ContextVar[str] = ContextVar("request_id", default="")


def current_request_id() -> str:
    return _request_id.get()


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        token = _request_id.set(request_id)
        try:
            response = await call_next(request)
            response.headers["x-request-id"] = request_id
            return response
        finally:
            _request_id.reset(token)


class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    """Bind one session per request, committing only on a clean response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            session = new_session()
        except DatabaseNotConfiguredError:
            # Proceed unbound rather than failing every route. `/health` needs to
            # be able to *report* a missing database, and an unauthenticated
            # request should get its 401 rather than a misleading 503. Any
            # handler that actually touches the database still raises from
            # `session_scope()`, which maps to 503.
            return await call_next(request)

        try:
            with bind_session(session):
                response = await call_next(request)
            # A handled 4xx/5xx is still a failed request; committing partial
            # writes behind an error response is how inconsistent state is born.
            if response.status_code < 400:
                session.commit()
            else:
                session.rollback()
            return response
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
