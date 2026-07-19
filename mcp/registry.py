"""MCP client registry: the six named clients and their sprint status.

Routing rule (contracts/mcp/README.md): internal tools for business logic and
computation; MCP only for external capabilities or live information."""

from mcp.clients.browser import BrowserMCPClient
from mcp.clients.calendar import CalendarMCPClient
from mcp.clients.email import EmailMCPClient
from mcp.clients.flights import FlightSearchMCPClient
from mcp.clients.hotels import HotelSearchMCPClient
from mcp.clients.playwright import PlaywrightMCPClient

# Instantiable today (stubs returning typed pending errors)
STUB_CLIENTS = {
    "browser": BrowserMCPClient,
    "playwright": PlaywrightMCPClient,
}

# Interface-only (abstract; implementations are future roadmap items)
INTERFACE_CLIENTS = {
    "email": EmailMCPClient,
    "calendar": CalendarMCPClient,
    "flight_search": FlightSearchMCPClient,
    "hotel_search": HotelSearchMCPClient,
}


def get_stub_client(name: str):
    if name not in STUB_CLIENTS:
        raise KeyError(
            f"'{name}' is not an instantiable MCP client; "
            f"stubs: {list(STUB_CLIENTS)}, interfaces: {list(INTERFACE_CLIENTS)}"
        )
    return STUB_CLIENTS[name]()
