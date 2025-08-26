from abc import ABC, abstractmethod

from fastmcp import FastMCP
from python_a2a import A2AServer, run_server

from core.utils.async_lib import continuous_process


class Tool(ABC):
    def __init__(self, mcp_server: FastMCP):
        self._mcp = mcp_server

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

class A2ATool(A2AServer, Tool, ABC):
    """
    Abstract base class for tools that can be registered with the FastMCP server.
    This class provides a common interface for tool registration and access to the MCP server instance.
    """
    def __init__(self, mcp_server: FastMCP, **kwargs):
        """
        Initialize the tool with the MCP server instance.
        :param mcp_server: The FastMCP server instance.
        :return: None
        """
        super().__init__(**kwargs)
        Tool.__init__(self, mcp_server)

    async def _get_capabilities(self) -> dict:
        return {
            "mcp_capability": await Tool._get_capabilities(self),
            "a2a_capability": self.agent_card.to_dict()
        }

    @continuous_process
    def run(self, host: str, port: int, **kwargs):
        self.agent_card.url = f"http://{host}:{port}"
        run_server(self, host, port, **kwargs)