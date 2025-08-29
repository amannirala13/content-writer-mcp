"""
@author: amannirala13
@date: 2025-8-23
@description: This module defines the AssignAuthor tool for assigning topics to the most suitable author based on their expertise.
             It utilizes the FastMCP framework for tool registration and the OpenAIClient for language model interactions.
"""

from fastmcp import FastMCP
from python_a2a import skill, agent

from core.utils.encoders.transport_encoder import transportify
from llm.provider.local_lm_client import LocalLMClient
from llm.provider.open_ai import OpenAIClient
from core.foundation.tools import A2ATool, MCPTool


@agent(
    name="AssignAuthor",
    version="1.0.0",
    description="A tool for assigning topics to the most suitable author based on their expertise.",
    tags=["tool", "author", "assignment", "expertise", "topic"],
)
class AssignAuthor(A2ATool, MCPTool):

    @skill(
        name="get_capabilities_skill",
        description="Get the capabilities of the AssignAuthor tool.",
        tags=["tool", "capabilities", "info"],
    )
    async def get_capabilities_skill(self) -> dict:
        return await self._get_capabilities()

    def __init__(self, mcp_server: FastMCP):
        """
        Initialize the AssignAuthor tool with the MCP server and OpenAI client.
        :param mcp_server: The FastMCP server instance.
        :return: None
        """
        A2ATool.__init__(self, mcp_server)
        MCPTool.__init__(self, mcp_server)
        self._llm_client = LocalLMClient()

    async def get_capabilities(self) -> dict:
        return {
            "mcp_capability": transportify(await MCPTool._get_capabilities(self)),
            "a2a_capability": transportify(await A2ATool._get_capabilities(self)),
        }

    def register_tool(self) -> None:
        """
        Register the assign_author tool with the MCP server.
        :return: None
        """

        @self.get_mcp().tool(
            name=f"{self.tool_mcp_path_prefix}r.assign_author",
            title=f"{self.tool_mcp_path_prefix}.assign_author",
            description="Assign the most suitable author for a given topic based on their expertise.",
        )
        async def assign_author(topic: str, authors: list) -> str:
            """
            Assign the most suitable author for a given topic.

            :param topic: The topic to be assigned.
            :param authors: A list of authors with their expertise.
            :return: The name of the most suitable author.
            """
            prompt = "You are an expert in assigning topics to authors based on their expertise. Given the topic from the user, assign the most suitable author from the following list:\n"
            for author in authors:
                prompt += f"- {author}\n"
            prompt += "The most suitable author is:"

            self._llm_client.define_system_behavior(prompt)

            response = await self._llm_client.generate_text_with_messages(
                config={
                    "model": "ibm/granite-3.2-8b",
                    "max_tokens": 50,
                },
                messages=[OpenAIClient.user_message(topic)],
            )
            return transportify(response)

        @self.get_mcp().tool(
            name=f"{self.tool_mcp_path_prefix}.get_capabilities",
            title=f"{self.tool_mcp_path_prefix}.get_capabilities",
            description="Get the capabilities of the AssignAuthor tool.",
        )
        async def get_capabilities() -> dict:
            return transportify(await self.get_capabilities())
