"""FastAPI application (BUILD_SPEC §2, §3, §9).

Middleware order is load-bearing. Starlette makes each `add_middleware` call
the new outermost layer, so registering in the order below produces an inbound
order of:

    CORS  ->  request context  ->  database session  ->  auth  ->  route

Request context is outside auth so that a 401 still carries a `request_id` in
its envelope — an unauthenticated failure is exactly the kind a user reports.
The session layer is outside auth so that one place guarantees commit-on-success
and rollback-on-failure; it costs a session object for requests auth rejects,
but SQLAlchemy does not open a connection until the first statement, so a
rejected request never reaches the database.

Domain exceptions are translated centrally (`backend/api/responses.py`) so no
router raises `HTTPException`.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import auth, health, knowledge, portfolio, preferences
from backend.api.chat import chat_router, rec_router
from backend.api.responses import HANDLED_EXCEPTIONS, error_response, request_id_of
from backend.config.settings import get_settings
from backend.middleware.auth import JWTAuthMiddleware
from backend.middleware.request_context import DatabaseSessionMiddleware, RequestContextMiddleware
from contracts.api.envelope import failure


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="RewardsPilotOS API", version="0.1.0")

    app.add_middleware(JWTAuthMiddleware)
    app.add_middleware(DatabaseSessionMiddleware)
    app.add_middleware(RequestContextMiddleware)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    for router in (
        health.router,
        auth.router,
        portfolio.router,
        preferences.router,
        knowledge.router,
        chat_router,
        rec_router,
    ):
        app.include_router(router)

    async def handle_domain_error(request: Request, exc: Exception) -> JSONResponse:
        return error_response(request, exc)

    # Registered per type: FastAPI's exception_handler takes one class, and
    # passing a tuple fails silently at lookup rather than at registration.
    for exc_type in HANDLED_EXCEPTIONS:
        app.add_exception_handler(exc_type, handle_domain_error)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # FastAPI's default validation response bypasses the envelope; a client
        # should not have to parse two response shapes.
        return JSONResponse(
            status_code=422,
            content=failure(
                "validation_error",
                "request body or parameters failed validation",
                request_id_of(request),
                details={"errors": exc.errors()},
            ),
        )

    return app


app = create_app()
