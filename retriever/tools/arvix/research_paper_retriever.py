from typing import List, Any

from python_a2a import skill

from core.foundation.tools import A2ATool, MCPTool


class ResearchPaperRetriever(A2ATool, MCPTool):

    def __init__(self, mcp_server):
        A2ATool.__init__(self, mcp_server)
        MCPTool.__init__(self, mcp_server)

    @skill(
        name="get_capabilities_skill",
        description="Get the capabilities of the ResearchPaperRetriever tool.",
        tags=["tool", "capabilities", "info"],
    )
    async def get_capabilities_skill(self) -> dict:
        return await self._get_capabilities()

    def register_tool(self):
        @MCPTool.get_mcp(self).tool(
            name=f"{self.tool_mcp_path_prefix}.retrieve_papers",
            title="Research Paper Retriever",
            description="A tool to retrieve research papers from Arxiv"
        )
        def retrieve_papers(query: str, max_results: int = 5) -> List[Any]:
            """
            Retrieve research papers from Arxiv based on a query.

            :param query: The search query for the research papers.
            :param max_results: The maximum number of results to return.
            :return: A list of research papers matching the query.
            """
            # Placeholder for actual retrieval logic
            return [{"title": f"Paper {i+1} on {query}", "abstract": "Abstract of the paper"} for i in range(max_results)]

        @MCPTool.get_mcp(self).tool(
            name=f"{self.tool_mcp_path_prefix}.get_capabilities",
            title=f"{self.tool_mcp_path_prefix}.get_capabilities",
            description="Get the capabilities of the ResearchPaperRetriever tool."
        )
        async def get_capabilities() -> dict:
            return await self._get_capabilities()