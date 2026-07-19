"""MCP layer: stub pending errors, capability validation, interface-only."""

import pytest

from contracts.mcp.base import MCPRequest
from mcp.clients.browser import BrowserMCPClient
from mcp.clients.email import EmailMCPClient
from mcp.clients.playwright import PlaywrightMCPClient
from mcp.registry import INTERFACE_CLIENTS, STUB_CLIENTS, get_stub_client


@pytest.mark.parametrize("client_cls", [BrowserMCPClient, PlaywrightMCPClient])
def test_stub_clients_return_typed_pending_errors(client_cls):
    client = client_cls()
    response = client.execute(MCPRequest(capability=client.capabilities[0]))
    assert response.status == "pending"
    assert response.error.code == "pending_integration"
    assert response.error.retryable is False
    assert response.server == client.server_name


def test_unknown_capability_is_structured_failure():
    response = BrowserMCPClient().execute(MCPRequest(capability="calculate_rewards"))
    assert response.status == "failed"
    assert response.error.code == "invalid_response"
    assert "not provided" in response.error.message


def test_interface_only_clients_cannot_be_instantiated():
    for client_cls in INTERFACE_CLIENTS.values():
        with pytest.raises(TypeError):
            client_cls()


def test_registry_split_and_lookup():
    assert set(STUB_CLIENTS) == {"browser", "playwright"}
    assert set(INTERFACE_CLIENTS) == {"email", "calendar", "flight_search", "hotel_search"}
    assert get_stub_client("browser").server_name == "browser"
    with pytest.raises(KeyError):
        get_stub_client("email")


def test_email_interface_declares_capabilities():
    assert "search_messages" in EmailMCPClient.capabilities
