"""Calendar MCP client (future, MASTER_SPEC ch. 22): reward expiry alerts,
annual fee reminders, promotion end dates.

Interface-only: defines the contract; no implementation ships in the sprint."""

from abc import abstractmethod

from contracts.mcp.base import MCPRequest, MCPResponse
from mcp.clients.base import MCPClientBase


class CalendarMCPClient(MCPClientBase):
    server_name = "calendar"
    capabilities = ("create_reminder", "list_reminders", "delete_reminder")

    @abstractmethod
    def _dispatch(self, request: MCPRequest) -> MCPResponse: ...
