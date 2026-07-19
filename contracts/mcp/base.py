"""MCP client/server contracts (BUILD_SPEC §8, MASTER_SPEC ch. 22).

MCP is the external integration layer only: it never calculates rewards,
makes recommendations, executes business rules, stores memory, or performs
graph optimization.

Routing rule (deterministic wherever possible): the Planner prefers internal
tools for business logic and computation; MCP is selected ONLY when external
capabilities or live information are required."""

from typing import Literal

from pydantic import BaseModel, Field


class MCPRequest(BaseModel):
    capability: str  # e.g. "fetch_page", "run_script", "search_awards"
    payload: dict = Field(default_factory=dict)
    timeout_s: float = Field(default=30.0, gt=0)


class MCPError(BaseModel):
    code: Literal[
        "pending_integration",  # stub: real server not wired yet (sprint state)
        "timeout",
        "auth_failure",
        "service_unavailable",
        "invalid_response",
        "rate_limited",
    ]
    message: str
    retryable: bool


class MCPResponse(BaseModel):
    server: str
    capability: str
    status: Literal["success", "failed", "pending"]
    data: dict | None = None
    error: MCPError | None = None
    latency_ms: float = 0.0
