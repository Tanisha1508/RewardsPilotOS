"""Hotel Search MCP client (future, MASTER_SPEC ch. 22): hotel award
availability and cash vs points comparison.

Interface-only: defines the contract; no implementation ships in the sprint."""

from abc import abstractmethod

from contracts.mcp.base import MCPRequest, MCPResponse
from mcp.clients.base import MCPClientBase


class HotelSearchMCPClient(MCPClientBase):
    server_name = "hotel_search"
    capabilities = ("search_availability", "compare_cash_vs_points")

    @abstractmethod
    def _dispatch(self, request: MCPRequest) -> MCPResponse: ...
