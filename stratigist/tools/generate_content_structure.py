"""
@author: amannirala13
@date: 2025-8-23
@description: This module defines the GenerateContentStructure tool for generating a structured content outline based on a given topic.
             It utilizes the FastMCP framework for tool registration and the OpenAIClient for language model interactions.
"""
from docutils.parsers.rst.directives.body import Topic
from fastmcp import FastMCP
from python_a2a import skill, agent

from core.utils.open_ai_schema_processor import process_openai_json_schema
from llm.llm_agent import LLMAgent
from llm.provider.local_lm_client import LocalLMClient
from llm.provider.open_ai import OpenAIClient
from models.content_structure_model import ContentStructureModel
from tools.tool import A2ATool


@agent(
    name="ContentStrategist",
    version="1.0.0",
    description="A tool for generating a structured content outline based on a given topic.",
    tags=["tool", "content", "structure", "outline", "topic", "strategy"],
)
class ContentStrategist(A2ATool):
    """
    A tool for generating a structured content outline based on a given topic.
    This tool utilizes the FastMCP framework for tool registration and the OpenAIClient for language model interactions.
    """
    def __init__(self, mcp_server: FastMCP):
        """
        Initialize the GenerateContentStructure tool with the MCP server and OpenAI client.
        :param mcp_server: The FastMCP server instance.
        :return: None
        """
        super().__init__(mcp_server)
        self._llm_client: LLMAgent = LocalLMClient(
            config = {"model": "gpt-5-nano",
                      "response_format": {
                          "type": "json_schema",
                          "json_schema": {
                              "name": "ContentStructure",
                              "schema": process_openai_json_schema(ContentStructureModel.model_json_schema()),
                              "strict": True
                          }
                      }
                      },
            system_behavior=f'''
                        You are an expert content strategist. Extract the main objective from the given content.
                        Provide different topics and aspects of the objective if applicable.
                        Define relevant images, charts, tables, or code snippets that could be included to enhance the content if applicable.
                        Proved a clear structure of topics and subtopics to be discussed/included if applicable.
                        Respond in a concise manner.
                        
                        Format your response in the following JSON schema:
                        
                        {ContentStructureModel.model_json_schema()}
                        
                        Ensure the JSON is properly formatted.
                        '''
        )

    @skill(
        name="generate_content_structure_skill",
        description="Generate a structured content outline based on the given topic.",
        tags=["tool", "content", "structure", "outline", "topic", "strategy"],
    )
    async def generate_content_structure_skill(self, topic: str) -> str:
        """
        Generate a structured content outline based on the given topic.
        :param topic: The topic to generate the content structure for.
        :return: A JSON string representing the structured content outline.
        """
        response = await self._llm_client.generate_text_with_messages(
            messages=[
                OpenAIClient.user_message(
                    f"Analyze the following topic and extract its main objective along with relevant topics and subtopics:\n\n{topic}"
                )
            ]
        )

        print("Raw response: ", response)
        content_structure = ContentStructureModel.model_validate_json(response)
        return content_structure.model_dump_json(indent=4)


    @skill(
        name="get_capabilities_skill",
        description="Get the capabilities of the ContentStrategist tool.",
        tags=["tool", "capabilities", "info"],
    )
    async def get_capabilities_skill(self) -> dict:
        return await self._get_capabilities()


    def register_tool(self) -> None:
        """
        Register the generate_content_structure tool with the MCP server.
        :return: None
        """
        @self.get_mcp().tool(
            name=f"{self.__class__.__name__}.generate_content_structure",
            title=f"{self.__class__.__name__}.generate_content_structure",
            description="Generate a structured content outline based on the given topic.",
            tags={"tool", "content", "structure", "outline", "topic", "strategy"},
        )
        async def generate_content_structure(topic: str) -> str:
            return await self.generate_content_structure_skill(topic)

        @self.get_mcp().tool(
            name=f"{self.__class__.__name__}.get_capabilities",
            title=f"{self.__class__.__name__}.get_capabilities",
            description="Get the capabilities of the ContentStrategist tool.",
            tags={"tool", "capabilities", "info"},
        )
        async def get_capabilities() -> dict:
            return await self._get_capabilities()