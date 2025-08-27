from core.foundation.look_up_service_registry import LookupServiceRegistryMCPTool
from retriever.tools.arvix.research_paper_retriever import ResearchPaperRetriever
from core.foundation.base_server import BaseServer
from stratigist.tools.generate_content_structure import ContentStrategist
from tools.routers.assign_author import AssignAuthor


class MServer(BaseServer):
    def __init__(self, host: str, port: int, name="Content Writer"):
        BaseServer.__init__(self, host = host, port = port, name = name)
        research_paper_retriever: ResearchPaperRetriever = ResearchPaperRetriever(mcp_server=self.get())
        content_integration_tool: ContentStrategist = ContentStrategist(mcp_server=self.get())
        assign_author: AssignAuthor = AssignAuthor(mcp_server=self.get())
        lookup_registry: LookupServiceRegistryMCPTool = LookupServiceRegistryMCPTool(mcp_server=self.get(),
                                                                                     registry_url="http://127.0.0.1:7001/mcp")

        self.load_default_tools([research_paper_retriever, content_integration_tool, assign_author, lookup_registry])
        self.register_tools()
