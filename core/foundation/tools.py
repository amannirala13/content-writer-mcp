import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager

from fastmcp import FastMCP, Client
from fastmcp.client import StreamableHttpTransport
from python_a2a import A2AServer, run_server

from client.client import MyClient
from core.foundation.models.tools_model import ToolsModel
from core.utils.async_lib import continuous_process


class MCPTool(ABC):
    def __init__(self, mcp_server: FastMCP):
        self._mcp = mcp_server
        self.tool_mcp_path_prefix = f"{self._mcp.name}.{self.__class__.__name__}"

    def get_mcp(self) -> FastMCP:
        return self._mcp

    async def _get_capabilities(self) -> dict:
        return {
                "name": self.get_mcp().name,
                "version": self.get_mcp().version,
                "tools": str(await self.get_mcp().get_tools()),
                "resources": str(await self.get_mcp().get_resources()),
                "prompts": str(await self.get_mcp().get_prompts()),
        }

    async def get_capabilities(self) -> dict:
        return await self._get_capabilities()

    @abstractmethod
    def register_tool(self) -> None:
        pass

'''
--------------------------------------------------------------
---------------------- [ A2A Tool ] --------------------------
--------------------------------------------------------------
'''

class A2ATool(A2AServer, ABC):
    """
    Abstract base class for tools that can be registered with the FastMCP server.
    This class provides a common interface for tool registration and access to the MCP server instance.
    """
    def __init__(self, mcp_server: FastMCP, **kwargs):
        super().__init__(**kwargs)

    async def _get_capabilities(self) -> dict:
        return  self.agent_card.to_dict()

    async def get_capabilities(self) -> dict:
        return await self._get_capabilities()

    @continuous_process
    def run(self, host: str, port: int, **kwargs):
        self.agent_card.url = f"http://{host}:{port}"
        run_server(self, host, port, **kwargs)


class LookupServiceRegistry:

    def __init__(self, mcp_server: FastMCP, registry_url: str):
        self.mcp = mcp_server
        self._registry_url: str = registry_url

    @asynccontextmanager
    async def _client(self):
        async with Client(StreamableHttpTransport(url=self._registry_url)) as c:
            yield c

    async def _get_capabilities(self) -> dict:
        async with self._client() as client:
            capability = await client.call_tool(f"service_registry.get_capabilities")
            return capability.structured_content

    async def get_capabilities(self) -> dict:
        return await self._get_capabilities()

    # async def connect_client(self):
    #     await self.client.connect()

    async def lookup_service(self, registry_id: str) -> ToolsModel | None:
        async with self._client() as client:
            result = await client.call_tool("service_registry.get_tool",
                                            arguments={"registry_id": registry_id})
            return ToolsModel.model_validate(result.structured_content)

    async def register_service(self, service: ToolsModel) -> None:
        async with self._client() as client:
            client.call_tool(f"service_registry.add_tool_to_registry",
                             arguments={"tool": service.model_dump()})

    async def list_services(self) -> dict[str, ToolsModel] | None:
        async with self._client() as client:
            result = await client.call_tool(f"service_registry.list_tools")
            print("This is raw result from list_services:", result)
            tools = {}
            for reg_id, item in result.structured_content.items():
                tools[reg_id] = ToolsModel.model_validate(item).model_dump()
            print("Parsed tools:", tools)
            return tools

