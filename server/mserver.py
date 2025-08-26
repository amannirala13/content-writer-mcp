import asyncio

from fastmcp import FastMCP
from python_a2a import run_server

from retriever.tools.arvix.research_paper_retriever import ResearchPaperRetriever
from server.base_server import BaseServer
from stratigist.tools.generate_content_structure import ContentStrategist
from tools.routers.assign_author import AssignAuthor


class MServer(BaseServer):
    def __init__(self, host: str, port: int, name="Content Writer"):
        super().__init__(host, port, name)
        research_paper_retriever: ResearchPaperRetriever = ResearchPaperRetriever(mcp_server=self.get())
        content_integration_tool: ContentStrategist = ContentStrategist(mcp_server=self.get())
        assign_author: AssignAuthor = AssignAuthor(mcp_server=self.get())

        self.load_default_tools([research_paper_retriever, content_integration_tool, assign_author])
        self.register_tools()
