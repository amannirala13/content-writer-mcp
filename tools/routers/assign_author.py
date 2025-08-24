"""
@author: amannirala13
@date: 2025-8-23
@description: This module defines the AssignAuthor tool for assigning topics to the most suitable author based on their expertise.
             It utilizes the FastMCP framework for tool registration and the OpenAIClient for language model interactions.
"""

from fastmcp import FastMCP

from llm.provider.open_ai import OpenAIClient
from tools.tools import Tools


class AssignAuthor(Tools):
    def __init__(self, mcp_server: FastMCP):
        """
        Initialize the AssignAuthor tool with the MCP server and OpenAI client.
        :param mcp_server: The FastMCP server instance.
        :return: None
        """
        super().__init__(mcp_server)
        self._llm_client = OpenAIClient()

    def register_tool(self) -> None:
        """
        Register the assign_author tool with the MCP server.
        :return: None
        """

        @self.get_mcp().tool()
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
                    "model": "gpt-4o-mini",
                    "max_tokens": 50,
                },
                messages=[OpenAIClient.user_message(topic)],
            )
            return response
