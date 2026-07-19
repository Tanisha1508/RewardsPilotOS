"""Browser MCP client: live issuer page retrieval (MASTER_SPEC ch. 22).

Stub implementation — every capability returns a typed pending error until
the real server is wired (deferred final-day piece)."""

from contracts.mcp.base import MCPRequest, MCPResponse
from mcp.clients.base import MCPClientBase


class BrowserMCPClient(MCPClientBase):
    server_name = "browser"
    capabilities = ("fetch_page", "fetch_promotion_page", "fetch_terms")

    def _dispatch(self, request: MCPRequest) -> MCPResponse:
        return self._pending(request)
