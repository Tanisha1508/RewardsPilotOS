"""Health check (BUILD_SPEC §9: DB, ChromaDB, Redis, LLM ping).

Unconfigured dependencies report `"not_configured"`, never `"ok"`. A health
endpoint that returns green for a subsystem it never contacted is worse than
no health endpoint — it is the one thing a deploy is trusted on.

Only the checks D2 actually wires are live: Postgres is pinged; ChromaDB,
Redis, and the LLM report their configuration state and are pinged in D3–D5
when they are wired. `status` is `ok` only when nothing checked is failing.
"""

from fastapi import APIRouter, Request
from sqlalchemy import text

from backend.api.responses import ok
from backend.config.settings import get_settings
from database.postgres.session import DatabaseNotConfiguredError, session_scope

router = APIRouter(prefix="/api/v1/health", tags=["health"])


def _check_database() -> str:
    try:
        with session_scope() as session:
            session.execute(text("SELECT 1"))
        return "ok"
    except DatabaseNotConfiguredError:
        return "not_configured"
    except Exception as exc:  # a failing DB is the point of the check
        return f"error: {type(exc).__name__}"


@router.get("")
def health(request: Request):
    settings = get_settings()
    checks = {
        "database": _check_database(),
        # Configuration state, not liveness — labelled so nobody reads these as
        # successful pings before D3–D5 wire them.
        "chromadb": "not_checked_until_d3",
        "redis": "ok_configured" if settings.redis_url else "not_configured",
        "llm": "ok_configured" if settings.gemini_api_key else "not_configured",
    }
    failing = [name for name, value in checks.items() if value.startswith("error")]
    return ok(request, {"status": "degraded" if failing else "ok", "checks": checks})
