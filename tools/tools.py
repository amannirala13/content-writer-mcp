"""
@author: amannirala13
@date: 2025-8-23
@description: This module defines an abstract base class for tools that can be registered with the FastMCP server.
             It provides a common interface for tool registration and access to the MCP server instance.
"""
from abc import ABC, abstractmethod

from fastmcp import FastMCP


class Tools(ABC):
    """
    Abstract base class for tools that can be registered with the FastMCP server.
    This class provides a common interface for tool registration and access to the MCP server instance.
    """
    def __init__(self, mcp_server: FastMCP):
        """
        Initialize the tool with the MCP server instance.
        :param mcp_server: The FastMCP server instance.
        :return: None
        """
        self._mcp = mcp_server

    # get the server instance
    def get_mcp(self) -> FastMCP:
        """
        Get the MCP server instance.
        :return: The FastMCP server instance.
        """
        return self._mcp

    # register a tool
    @abstractmethod
    def register_tool(self) -> None:
        """
        Register the tool with the MCP server.
        :return: None
        """
        pass