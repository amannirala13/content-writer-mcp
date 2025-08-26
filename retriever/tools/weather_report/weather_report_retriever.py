from typing import Any, Dict
import httpx
from python_a2a import skill
from tools.tool import A2ATool


class WeatherRetriever(A2ATool):
    """
    Tool to fetch current weather (temperature and wind speed) for any latitude and longitude
    using the Open-Meteo API.
    """

    API_URL_TEMPLATE = "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m"

    @skill(
        name="get_capabilities_skill",
        description="Get the capabilities of the WeatherRetriever tool.",
        tags=["tool", "capabilities", "info"],
    )
    async def get_capabilities_skill(self) -> dict:
        return await self._get_capabilities()

    @skill(
        name="get_current_weather",
        description="Get current temperature and wind speed for a given latitude and longitude.",
        tags=["weather", "forecast", "temperature", "wind"],
    )
    async def get_current_weather(
        self, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        """
        Fetch current weather for the given latitude and longitude.

        :param latitude: Latitude of the location
        :param longitude: Longitude of the location
        :return: Dictionary containing temperature and wind speed
        """
        url = self.API_URL_TEMPLATE.format(lat=latitude, lon=longitude)
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        current = data.get("current", {})
        temperature = current.get("temperature_2m")
        wind_speed = current.get("wind_speed_10m")

        if temperature is None or wind_speed is None:
            return {"error": "Weather data not available for this location"}

        return {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "temperature_2m": temperature,
            "wind_speed_10m": wind_speed,
            "timezone": data.get("timezone"),
            "time": current.get("time"),
        }

    def register_tool(self):
        @self.get_mcp().tool(
            name=f"{self.__class__.__name__}.get_current_weather",
            title="Weather Retriever",
            description="A tool to get current weather for any location",
        )
        async def get_current_weather_tool(
            latitude: float, longitude: float
        ) -> Dict[str, Any]:
            return await self.get_current_weather(latitude, longitude)

        @self.get_mcp().tool(
            name=f"{self.__class__.__name__}.get_capabilities",
            title=f"{self.__class__.__name__}.get_capabilities",
            description="Get the capabilities of the WeatherRetriever tool.",
        )
        async def get_capabilities() -> dict:
            return await self._get_capabilities()
