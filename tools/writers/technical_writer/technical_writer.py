"""
@author: ShashankKothari-exe
@date: 2025-8-24
@description: This module defines a technical writing tool using a local Granite LLM agent.
             It implements the Tools interface and registers with the FastMCP server
             to provide documentation generation capabilities.
"""

from fastmcp import FastMCP, Request, Response
import tools.tools as Tools
from llm.provider.granite import (
    GraniteClient,
)  # Replace with actual local Granite agent path


class TechWriterTool(Tools):
    """
    A tool that uses a local Granite LLM agent to function as a technical writer.
    This tool can be registered with the FastMCP server to provide structured,
    professional writing for technical use cases like documentation, explanations, or summaries.
    """

    def __init__(self, mcp_server: FastMCP, granite_agent: GraniteClient):
        """
        Initialize the GraniteTechWriterTool with the MCP server and local Granite agent.
        :param mcp_server: The FastMCP server instance.
        :param granite_agent: The local GraniteClient instance for LLM interaction.
        """
        super().__init__(mcp_server)
        self._granite_agent = granite_agent

    def register_tool(self) -> None:
        """
        Register the technical writer tool with the FastMCP server under the route '/write/technical'.
        :return: None
        """

        @self._mcp.route("/write/technical", methods=["POST"])
        async def handle_technical_write(request: Request) -> Response:
            """
            Handle POST requests to generate technical content using Granite.
            Expected JSON payload: { "prompt": "Explain memory management in Rust." }
            """
            data = await request.json()
            prompt = data.get("prompt")

            if not prompt:
                return Response.json({"error": "Prompt is required."}, status=400)

            enhanced_prompt = (
                "You are a technical writer. Provide a clear, structured, and professional explanation.\n"
                f"Prompt: {prompt}"
            )

            try:
                response = await self._granite_agent.generate_text(enhanced_prompt)
                return Response.json({"output": response}, status=200)
            except Exception as e:
                return Response.json({"error": str(e)}, status=500)
