"""Playwright MCP client: browser automation (MASTER_SPEC ch. 22).

Stub implementation — every capability returns a typed pending error until
the real server is wired (deferred final-day piece)."""

from contracts.mcp.base import MCPRequest, MCPResponse
from mcp.clients.base import MCPClientBase


class PlaywrightMCPClient(MCPClientBase):
    server_name = "playwright"
    capabilities = ("navigate", "fill_form", "capture_screenshot", "extract_dynamic_content")

    def _dispatch(self, request: MCPRequest) -> MCPResponse:
        return self._pending(request)
