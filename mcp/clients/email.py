"""Email MCP client (future, MASTER_SPEC ch. 22): reward statements, promo
mail, expiry notices — with explicit user consent.

Interface-only: defines the contract; no implementation ships in the sprint."""

from abc import abstractmethod

from contracts.mcp.base import MCPRequest, MCPResponse
from mcp.clients.base import MCPClientBase


class EmailMCPClient(MCPClientBase):
    server_name = "email"
    capabilities = ("search_messages", "get_message", "list_reward_statements")

    @abstractmethod
    def _dispatch(self, request: MCPRequest) -> MCPResponse: ...
