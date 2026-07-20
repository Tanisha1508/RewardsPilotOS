"""The API response envelope (BUILD_SPEC §3).

    { "data": {...}, "error": null, "meta": { "request_id", "generated_at" } }

Every response goes through here, successes and failures alike, so a client
never has to branch on response shape to find out which it got — `error` is
null or it isn't.

It lives in `contracts/api/` rather than `backend/schemas/` because it is a
cross-boundary contract: the hand-written TypeScript client in
`frontend/types/api.ts` mirrors these fields, and the two must agree.
"""

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class Meta(BaseModel):
    request_id: str
    generated_at: str


class Envelope(BaseModel, Generic[T]):
    data: T | None = None
    error: ErrorBody | None = None
    meta: Meta


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def success(data: Any, request_id: str) -> dict:
    return {
        "data": data,
        "error": None,
        "meta": {"request_id": request_id, "generated_at": _now_iso()},
    }


def failure(
    code: str, message: str, request_id: str, details: dict[str, Any] | None = None
) -> dict:
    return {
        "data": None,
        "error": {"code": code, "message": message, "details": details},
        "meta": {"request_id": request_id, "generated_at": _now_iso()},
    }


class Created(BaseModel):
    """Returned by creates so the client has the id without a second fetch."""

    id: str


class Deleted(BaseModel):
    id: str
    deleted: bool = Field(default=True)
