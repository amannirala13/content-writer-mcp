import asyncio

from fastmcp import Client
from mcp.types import CallToolResult


class MyClient:
    def __init__(self, http_url: str):
        self.http_url = http_url
        self._client = None

    def __enter__(self):
        self._client: Client = Client(self.http_url)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._client is not None:
            asyncio.wait(self._client.close())
            self._client = None

    async def connect(self) -> None:
        if self._client is None:
            self._client = Client(self.http_url)
            await self._client.__aenter__()

    async def disconnect(self):
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def list_tools(self):
        if self._client is None:
            asyncio.run(self.connect())
        tools = await self._client.list_tools()
        return tools

    async def call_tool(self, tool_name: str, **kwargs) -> CallToolResult:
        if self._client is None:
            await self.connect()
        result = await self._client.call_tool(tool_name, kwargs)
        return result
