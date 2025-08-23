from abc import ABC, abstractmethod

from fastmcp import FastMCP


class Tools(ABC):
    def __init__(self, mcp_server: FastMCP):
        self._mcp = mcp_server

    # get the server instance
    def get_mcp(self) -> FastMCP: return self._mcp

    # register a tool
    @abstractmethod
    def register_tool(self) -> None:
        pass