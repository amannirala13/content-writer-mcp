import os
from typing import List

from fastmcp import FastMCP

from tools.generators.generate_content_structure import GenerateContentStructure
from tools.retrievers.arvix.research_paper_retriever import ResearchPaperRetriever
from tools.routers.assign_author import AssignAuthor
from tools.tools import Tools


class Server:
    def __init__(self, host: str, port: int, name="Content Writer"):
        self._host: str = host
        self._port: int = port
        self._mcp_server: FastMCP = FastMCP(name)

    def run(self):
        self._mcp_server.run(transport="http", host=self._host, port=self._port)

    def get(self):
        return self._mcp_server

    def register_tools(self):
        research_paper_retriever: Tools = ResearchPaperRetriever(mcp_server= self._mcp_server)
        content_integration_tool: Tools = GenerateContentStructure(mcp_server= self._mcp_server)
        assign_author: Tools = AssignAuthor(mcp_server= self._mcp_server)

        research_paper_retriever.register_tool()
        content_integration_tool.register_tool()
        assign_author.register_tool()