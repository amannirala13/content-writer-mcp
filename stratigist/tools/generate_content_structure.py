"""
@author: amannirala13
@date: 2025-8-23
@description: This module defines the GenerateContentStructure tool for generating a structured content outline based on a given topic.
             It utilizes the FastMCP framework for tool registration and the OpenAIClient for language model interactions.
"""
import asyncio

from asyncinit import asyncinit
from fastmcp import FastMCP
from lazy_object_proxy.utils import await_
from python_a2a import skill, agent

from core.foundation.look_up_service_registry import LookupServiceRegistryMCPTool
from core.foundation.models.content_structure_model import ContentStructureModel
from core.foundation.models.tools_model import ToolsModel, SupportedProtocolsEnum
from core.foundation.tools import A2ATool, LookupServiceRegistry, MCPTool
from core.utils.run_blocking import run_blocking
from llm.llm_agent import LLMAgent
from llm.provider.local_lm_client import LocalLMClient
from llm.provider.open_ai import OpenAIClient



@agent(
    name="ContentStrategist",
    version="1.0.0",
    description="A tool for generating a structured content outline based on a given topic.",
    tags=["tool", "content", "structure", "outline", "topic", "strategy"],
)
class ContentStrategist(MCPTool, A2ATool, LookupServiceRegistry):
    """
    A tool for generating a structured content outline based on a given topic.
    This tool utilizes the FastMCP framework for tool registration and the OpenAIClient for language model interactions.
    """

    def __init__(self, mcp_server: FastMCP, service_registry_url: str = None, **kwargs):
        A2ATool.__init__(self, mcp_server)
        MCPTool.__init__(self, mcp_server)
        LookupServiceRegistry.__init__(self, mcp_server,"http://127.0.0.1:7001/mcp")
        self._llm_client: LLMAgent = LocalLMClient(
            # config = {"model": "gpt-5-nano",
            #           "response_format": {
            #               "type": "json_schema",
            #               "json_schema": {
            #                   "name": "ContentStructure",
            #                   "schema": process_openai_json_schema(ContentStructureModel.model_json_schema()),
            #                   "strict": True
            #               }
            #           }
            #           },
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
    async def generate_content_structure_skill(self, topic: str) -> ContentStructureModel:
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
        return content_structure


    @skill(
        name="get_capabilities_skill",
        description="Get the capabilities of the ContentStrategist tool.",
        tags=["tool", "capabilities", "info"],
    )
    async def get_capabilities_skill(self) -> dict:
        return await self.get_capabilities()

    async def get_capabilities(self) -> dict:
        return {
            "mcp_capability": await MCPTool._get_capabilities(self),
            "a2a_capability": await A2ATool._get_capabilities(self),
            "registry_capability": await LookupServiceRegistry._get_capabilities(self)
        }

    async def register_self(self):
        capability = await self.get_capabilities()
        tool = ToolsModel(
            name="ContentStrategist",
            version="1.0.0",
            description="A tool for generating a structured content outline based on a given topic.",
            tags=["tool", "content", "structure", "outline", "topic", "strategy"],
            protocol=SupportedProtocolsEnum.A2A,
            capabilities=capability
        )
        await self.register_service(tool)

    def register_tool(self) -> None:
        """
        Register the generate_content_structure tool with the MCP server.
        :return: None
        """

        @MCPTool.get_mcp(self).tool(
            name=f"{self.tool_mcp_path_prefix}.generate_content_structure",
            title=f"{self.tool_mcp_path_prefix}.generate_content_structure",
            description="Generate a structured content outline based on the given topic.",
            tags={"tool", "content", "structure", "outline", "topic", "strategy"},
            output_schema=ContentStructureModel.model_json_schema()
        )
        async def generate_content_structure(topic: str) -> ContentStructureModel:
            return await self.generate_content_structure_skill(topic)

        @MCPTool.get_mcp(self).tool(
            name=f"{self.tool_mcp_path_prefix}.get_capabilities",
            title=f"{self.tool_mcp_path_prefix}.get_capabilities",
            description="Get the capabilities of the ContentStrategist tool.",
            tags={"tool", "capabilities", "info"},
        )
        async def get_capabilities() -> dict:
            return await self.get_capabilities()

        asyncio.run(self.register_self())