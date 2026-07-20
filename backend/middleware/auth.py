"""JWT bearer enforcement (BUILD_SPEC §3: auth on everything except `/health`
and auth routes).

The exemption list is a prefix allowlist checked against the *full* path, and
it is deliberately short. Two properties matter more than convenience:

1. **A new router is protected by default.** Mounting a route under
   `/api/v1/...` requires no opt-in to be authenticated — forgetting to add a
   dependency cannot expose data.
2. **Auth routes are exempt from the middleware, not from verification.**
   `/auth/sync` still verifies its token (via `verified_claims`); it is exempt
   only because the local `users` row may not exist yet, which is precisely
   what it is being called to fix.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.auth.tokens import AuthError, AuthNotConfiguredError, bearer_token, verify_token
from contracts.api.envelope import failure

PUBLIC_PREFIXES = (
    "/api/v1/health",
    "/api/v1/auth/",
    "/docs",
    "/redoc",
    "/openapi.json",
)


def is_public(path: str) -> bool:
    return any(path == p.rstrip("/") or path.startswith(p) for p in PUBLIC_PREFIXES)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if is_public(request.url.path):
            return await call_next(request)

        request_id = getattr(request.state, "request_id", "")
        try:
            claims = verify_token(bearer_token(request.headers.get("authorization")))
        except AuthError as exc:
            return JSONResponse(
                status_code=401,
                content=failure("unauthorized", str(exc), request_id),
            )
        except AuthNotConfiguredError as exc:
            # Misconfiguration, not a client error — and never a silent pass.
            return JSONResponse(
                status_code=503,
                content=failure("auth_not_configured", str(exc), request_id),
            )

        request.state.user_id = claims.user_id
        request.state.claims = claims
        return await call_next(request)
