import math
import pytest
import httpx
from unittest.mock import AsyncMock, Mock, patch
from retriever.tools.currency_rate.realtime_currency_rate_fetcher import (
    CurrencyExchangeRetriever,
)


@pytest.mark.asyncio
async def test_get_exchange_rate_success():
    retriever = CurrencyExchangeRetriever(FastMCP=None, mcp_server=None)

    fake_response = {"result": "success", "rates": {"USD": 1.08, "INR": 89.5}}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.json = Mock(return_value=fake_response)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_get.return_value = mock_response

        result = await retriever.get_exchange_rate("EUR", "INR")
        assert result["base"] == "EUR"
        assert result["target"] == "INR"
        assert math.isclose(result["rate"], 89.5)


@pytest.mark.asyncio
async def test_get_exchange_rate_currency_not_found():
    retriever = CurrencyExchangeRetriever(FastMCP=None, mcp_server=None)

    fake_response = {"result": "success", "rates": {"USD": 1.08}}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.json = Mock(return_value=fake_response)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_get.return_value = mock_response

        result = await retriever.get_exchange_rate("EUR", "INR")
        assert "error" in result
        assert "Currency INR not found" in result["error"]


@pytest.mark.asyncio
async def test_get_exchange_rate_http_error():
    retriever = CurrencyExchangeRetriever(FastMCP=None, mcp_server=None)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPStatusError(
            message="Error", request=None, response=None
        )

        with pytest.raises(httpx.HTTPStatusError):
            await retriever.get_exchange_rate("EUR", "INR")


@pytest.mark.asyncio
async def test_get_capabilities_skill_returns_dict():
    retriever = CurrencyExchangeRetriever(FastMCP=None, mcp_server=None)

    with patch.object(
        retriever, "_get_capabilities", AsyncMock(return_value={"name": "test"})
    ):
        result = await retriever.get_capabilities_skill()
        assert result == {"name": "test"}


@pytest.mark.asyncio
async def test_mcp_endpoint_registration_and_call_works():
    # Minimal dummy MCP server that behaves like FastMCP for .tool decorator
    class DummyMCP:
        def __init__(self):
            self.tools = {}

        def tool(self, name, title, description):
            def decorator(fn):
                self.tools[name] = fn
                return fn

            return decorator

    mcp = DummyMCP()
    retriever = CurrencyExchangeRetriever(
        mcp
    )  # pass only mcp_server as per A2ATool.__init__

    # Register MCP tools
    retriever.register_tool()

    # Ensure the exchange tool is registered under the expected name
    tool_name = f"{retriever.__class__.__name__}.get_exchange_rate"
    assert tool_name in mcp.tools, "MCP tool was not registered"

    # Mock the HTTP call so we don't hit the real API
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        fake_response = {"result": "success", "rates": {"INR": 90.0}}
        mock_resp = AsyncMock()
        mock_resp.json = Mock(return_value=fake_response)  # sync like real httpx
        mock_resp.raise_for_status = Mock(return_value=None)  # sync like real httpx
        mock_get.return_value = mock_resp

        # Call the registered MCP tool (it's an async function)
        result = await mcp.tools[tool_name]("EUR", "INR")

    assert result == {"base": "EUR", "target": "INR", "rate": 90.0}
