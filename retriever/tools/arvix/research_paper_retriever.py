from typing import List, Any

from fastmcp import FastMCP
from python_a2a import skill

from tools.tool import A2ATool


class ResearchPaperRetriever(A2ATool):

    @skill(
        name="get_capabilities_skill",
        description="Get the capabilities of the ResearchPaperRetriever tool.",
        tags=["tool", "capabilities", "info"],
    )
    async def get_capabilities_skill(self) -> dict:
        return await self._get_capabilities()

    def register_tool(self):
        @self.get_mcp().tool(
            name=f"{self.__class__.__name__}.retrieve_papers",
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

        @self.get_mcp().tool(
            name=f"{self.__class__.__name__}.get_capabilities",
            title=f"{self.__class__.__name__}.get_capabilities",
            description="Get the capabilities of the ResearchPaperRetriever tool."
        )
        async def get_capabilities() -> dict:
            return await self._get_capabilities()