"""Flight Search MCP client (future, MASTER_SPEC ch. 22): award availability,
flight pricing, airline schedules.

Interface-only: defines the contract; no implementation ships in the sprint."""

from abc import abstractmethod

from contracts.mcp.base import MCPRequest, MCPResponse
from mcp.clients.base import MCPClientBase


class FlightSearchMCPClient(MCPClientBase):
    server_name = "flight_search"
    capabilities = ("search_awards", "search_fares", "get_schedule")

    @abstractmethod
    def _dispatch(self, request: MCPRequest) -> MCPResponse: ...
