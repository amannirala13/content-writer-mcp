from typing import Any, Dict
import httpx
from python_a2a import skill
from tools.tool import A2ATool


class CurrencyExchangeRetriever(A2ATool):
    API_URL_TEMPLATE = "https://open.er-api.com/v6/latest/{base}"

    @skill(
        name="get_capabilities_skill",
        description="Get the capabilities of the CurrencyExchangeRetriever tool.",
        tags=["tool", "capabilities", "info"],
    )
    async def get_capabilities_skill(self) -> dict:
        return await self._get_capabilities()

    @skill(
        name="get_exchange_rate",
        description="Get the exchange rate from any base currency to any target currency.",
        tags=["currency", "exchange"],
    )
    async def get_exchange_rate(
        self, base_currency: str, target_currency: str
    ) -> Dict[str, Any]:
        """
        Fetch the current exchange rate between two currencies.

        :param base_currency: Base currency code (e.g. 'USD', 'EUR', 'INR').
        :param target_currency: Target currency code (e.g. 'EUR', 'INR').
        :return: Dictionary containing exchange rate information.
        """
        url = self.API_URL_TEMPLATE.format(base=base_currency.upper())
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        rates = data.get("rates", {})
        rate = rates.get(target_currency.upper())
        if rate is None:
            return {
                "error": f"Currency {target_currency.upper()} not found for base {base_currency.upper()}"
            }
        return {
            "base": base_currency.upper(),
            "target": target_currency.upper(),
            "rate": rate,
        }

    def register_tool(self):
        @self.get_mcp().tool(
            name=f"{self.__class__.__name__}.get_exchange_rate",
            title="Currency Exchange Retriever",
            description="A tool to get exchange rate between any two currencies",
        )
        async def get_exchange_rate_tool(
            base_currency: str, target_currency: str
        ) -> Dict[str, Any]:
            """
            Get exchange rate from a base currency to a target currency.

            :param base_currency: Base currency code (e.g. 'USD', 'EUR').
            :param target_currency: Target currency code (e.g. 'EUR', 'INR').
            :return: Dictionary containing exchange rate information.
            """
            return await self.get_exchange_rate(base_currency, target_currency)

        @self.get_mcp().tool(
            name=f"{self.__class__.__name__}.get_capabilities",
            title=f"{self.__class__.__name__}.get_capabilities",
            description="Get the capabilities of the CurrencyExchangeRetriever tool.",
        )
        async def get_capabilities() -> dict:
            return await self._get_capabilities()
