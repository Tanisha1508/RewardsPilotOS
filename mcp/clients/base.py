"""Common MCP client base contract (BUILD_SPEC §8).

Every client declares its server name and capability set; `execute` validates
the request against declared capabilities before dispatching. Stubs return
typed pending errors; interface-only clients define capabilities without an
implementation."""

import time
from abc import ABC, abstractmethod

from contracts.mcp.base import MCPError, MCPRequest, MCPResponse


class MCPClientBase(ABC):
    server_name: str = "unnamed"
    capabilities: tuple[str, ...] = ()

    def execute(self, request: MCPRequest) -> MCPResponse:
        started = time.monotonic()
        if request.capability not in self.capabilities:
            return MCPResponse(
                server=self.server_name,
                capability=request.capability,
                status="failed",
                error=MCPError(
                    code="invalid_response",
                    message=(
                        f"capability '{request.capability}' not provided by "
                        f"{self.server_name}; available: {list(self.capabilities)}"
                    ),
                    retryable=False,
                ),
            )
        response = self._dispatch(request)
        response.latency_ms = round((time.monotonic() - started) * 1000, 2)
        return response

    @abstractmethod
    def _dispatch(self, request: MCPRequest) -> MCPResponse: ...

    def _pending(self, request: MCPRequest) -> MCPResponse:
        """Typed pending error for stubbed servers (sprint milestone)."""
        return MCPResponse(
            server=self.server_name,
            capability=request.capability,
            status="pending",
            error=MCPError(
                code="pending_integration",
                message=(
                    f"{self.server_name} MCP server is not wired yet; live "
                    "integrations are the deferred final-day piece (BUILD_SPEC §8)"
                ),
                retryable=False,
            ),
        )
