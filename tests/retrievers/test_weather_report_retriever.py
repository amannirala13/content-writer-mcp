import math
import pytest
import httpx
from unittest.mock import AsyncMock, Mock, patch

from retriever.tools.weather_report.weather_report_retriever import WeatherRetriever


@pytest.mark.asyncio
async def test_get_current_weather_success():
    retriever = WeatherRetriever(mcp_server=None)

    fake_response = {
        "latitude": 52.52,
        "longitude": 13.41,
        "timezone": "GMT",
        "current": {
            "time": "2025-08-26T19:00",
            "temperature_2m": 20.4,
            "wind_speed_10m": 6.2,
        },
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.json = Mock(return_value=fake_response)  # sync like httpx
        mock_response.raise_for_status = Mock(return_value=None)
        mock_get.return_value = mock_response

        result = await retriever.get_current_weather(52.52, 13.41)
        assert math.isclose(result["latitude"], 52.52)
        assert math.isclose(result["longitude"], 13.41)
        assert math.isclose(result["temperature_2m"], 20.4)
        assert math.isclose(result["wind_speed_10m"], 6.2)
        assert result["timezone"] == "GMT"
        assert result["time"] == "2025-08-26T19:00"


@pytest.mark.asyncio
async def test_get_current_weather_data_missing():
    retriever = WeatherRetriever(mcp_server=None)

    fake_response = {"latitude": 52.52, "longitude": 13.41, "current": {}}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.json = Mock(return_value=fake_response)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_get.return_value = mock_response

        result = await retriever.get_current_weather(52.52, 13.41)
        assert "error" in result
        assert result["error"] == "Weather data not available for this location"


@pytest.mark.asyncio
async def test_get_current_weather_http_error():
    retriever = WeatherRetriever(mcp_server=None)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPStatusError(
            message="Error", request=None, response=None
        )

        with pytest.raises(httpx.HTTPStatusError):
            await retriever.get_current_weather(52.52, 13.41)


@pytest.mark.asyncio
async def test_get_capabilities_skill_returns_dict():
    retriever = WeatherRetriever(mcp_server=None)

    with patch.object(
        retriever, "_get_capabilities", AsyncMock(return_value={"name": "test"})
    ):
        result = await retriever.get_capabilities_skill()
        assert result == {"name": "test"}


@pytest.mark.asyncio
async def test_mcp_endpoint_registration_and_call_works():
    # Minimal dummy MCP server that mimics the .tool decorator
    class DummyMCP:
        def __init__(self):
            self.tools = {}

        def tool(self, name, title, description):
            def decorator(fn):
                self.tools[name] = fn
                return fn

            return decorator

    # Create the MCP server and tool
    mcp = DummyMCP()
    retriever = WeatherRetriever(mcp)  # pass only mcp_server

    # Register MCP tools
    retriever.register_tool()

    # Ensure the get_current_weather tool is registered
    tool_name = f"{retriever.__class__.__name__}.get_current_weather"
    assert tool_name in mcp.tools, "MCP tool was not registered"

    # Mock the HTTP call so we don't hit the real API
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        fake_response = {
            "latitude": 52.52,
            "longitude": 13.41,
            "timezone": "GMT",
            "current": {
                "time": "2025-08-26T19:00",
                "temperature_2m": 20.4,
                "wind_speed_10m": 6.2,
            },
        }
        mock_resp = AsyncMock()
        mock_resp.json = Mock(return_value=fake_response)
        mock_resp.raise_for_status = Mock(return_value=None)
        mock_get.return_value = mock_resp

        # Call the registered MCP tool function (async)
        result = await mcp.tools[tool_name](52.52, 13.41)

    # Use math.isclose for floating-point comparisons
    assert math.isclose(result["latitude"], 52.52)
    assert math.isclose(result["longitude"], 13.41)
    assert math.isclose(result["temperature_2m"], 20.4)
    assert math.isclose(result["wind_speed_10m"], 6.2)

    # Other fields can be checked normally
    assert result["timezone"] == "GMT"
    assert result["time"] == "2025-08-26T19:00"
