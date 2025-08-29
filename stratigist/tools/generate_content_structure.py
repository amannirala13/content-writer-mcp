"""
@author: amannirala13
@date: 2025-8-23
@description: This module defines the GenerateContentStructure tool for generating a structured content outline based on a given topic.
             It utilizes the FastMCP framework for tool registration and the OpenAIClient for language model interactions.
"""
from __future__ import annotations

from operator import inv
from typing import override

from fastmcp import FastMCP
from python_a2a import skill, agent

from core.foundation.models.content_structure_model import ContentStructureModel
from core.foundation.models.tools_model import ToolsModel, SupportedProtocolsEnum
from core.foundation.tools import A2ATool, LookupServiceRegistry, MCPTool, RegistryAwareMixin
from core.utils.encoders.transport_encoder import transportify
from core.utils.runtime_utils.idempoflight import idempotent, singleflight, topic_key
from llm.llm_agent import LLMAgent
from llm.provider.local_lm_client import LocalLMClient
from llm.provider.open_ai import OpenAIClient
from fastmcp import settings as mcp_settings


def _log(msg: str) -> None:
    print(f"[ContentStrategist] {msg}")

@agent(
    name="ContentStrategist",
    version="1.0.0",
    description="A tool for generating a structured content outline based on a given topic.",
    tags=["tool", "content", "structure", "outline", "topic", "strategy"],
)
class ContentStrategist(MCPTool, A2ATool, RegistryAwareMixin):
    """
    A tool for generating a structured content outline based on a given topic.
    This tool utilizes the FastMCP framework for tool registration and the OpenAIClient for language model interactions.
    """
    def __init__(self, mcp_server: FastMCP, service_registry_url: str = None, **kwargs):
        A2ATool.__init__(self, mcp_server)
        MCPTool.__init__(self, mcp_server)
        RegistryAwareMixin.__init__(self, mcp_server, "http://127.0.0.1:7001/mcp")
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
                        ---
                        <limitations>
                            <limitation>Do not include any explanations or additional text outside the JSON structure.</limitation>
                            <limitation>Only respond in JSON format following the provided schema.</limitation>
                            <limitation>World limit for the entire response is 300 words.</limitation>
                            <limitation>Ezure that params images, charts, tables, code_snippets are lists.</limitation>
                            <limitation>Strictly follow the JSON schema provided.</limitation>
                            <limitation>Ensure the JSON is properly formatted.</limitation>
                            <limitation>If a field is not applicable,use the default value if proposed in the schema, nothing should be null or undefined.</limitation>
                        </limitations>
                        ---
                        <output-json-schema>
                                {ContentStructureModel.model_json_schema()}
                        </output-json-schema>
                        ---
                        <non-negotiable-instruction>
                            Format your response in the following JSON schema:
                        </non-negotiable-instruction>
                        ---
                        <strict-instructions>
                            <instruction>Do not include any explanations or additional text outside the JSON structure.</instruction>
                            <instruction>Only respond in JSON format following the provided schema.</instruction>
                            <instruction>Ensure that params images, charts, tables, and code_snippets are lists.</instruction>
                            <instruction>Strictly follow the JSON schema provided.</instruction>
                            <instruction>Ensure the JSON is properly formatted.</instruction>
                            <instruction>If a field is not applicable, use the default value if proposed in the schema; nothing should be null or undefined.</instruction>
                            <instruction>Enforce the limitations strictly without negotiation</instruction>
                        </strict-instructions>
                        '''
        )

    @override
    async def ping(self) -> str:
        await self.ensure_registered()
        return await super().ping()

    @override
    async def build_tools_model(self) -> ToolsModel:
        capability = await self.get_capabilities()
        tool = ToolsModel(
            registry_id=f"{self.get_mcp().name}{self.__class__.__name__}",
            name="ContentStrategist",
            version="1.0.0",
            description="A tool for generating a structured content outline based on a given topic.",
            tags=["tool", "content", "structure", "outline", "topic", "strategy"],
            protocol=SupportedProtocolsEnum.A2A,
            capabilities=capability,
            endpoint=f"http://{mcp_settings.host}:{mcp_settings.port}/mcp"
        )
        return tool

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
        print(f"[gen_content] inv={inv} topic_hash={hash(topic)} session={mcp_settings.port}")
        response = await self._llm_client.generate_text_with_messages(
            messages=[
                OpenAIClient.user_message(
                    f"Analyze the following topic and extract its main objective along with relevant topics and subtopics:\n\n{topic}"
                )
            ]
        )

        print("Raw response: ", response)
        content_structure = ContentStructureModel.model_validate_json(response)
        return transportify(content_structure)


    @skill(
        name="get_capabilities_skill",
        description="Get the capabilities of the ContentStrategist tool.",
        tags=["tool", "capabilities", "info"],
    )
    async def get_capabilities_skill(self) -> dict:
        await self.ensure_registered()
        return await self.get_capabilities()

    async def get_capabilities(self) -> dict:
        return {
            "mcp_capability": transportify(await MCPTool._get_capabilities(self)),
            "a2a_capability": transportify(await A2ATool._get_capabilities(self)),
            "registry_capability": transportify(await LookupServiceRegistry._get_capabilities(self))
        }

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
            output_schema=ContentStructureModel.model_json_schema(),
            meta = {
                "example": {
                    "topic": "Your topic here (mandatory)",
                    "request_id": "optional-unique-request-id (recommended)"
                }
            }
        )
        @idempotent(
            ttl=60,
            key_func=lambda topic, request_id=None: topic_key(
                self.__class__.__name__, "generate_content", request_id, topic
            )
        )
        @singleflight(
            key_func=lambda topic, request_id=None: topic_key(
                self.__class__.__name__, "generate_content", request_id, topic
            )
        )
        async def generate_content_structure(
                topic: str,
                *,
                request_id: str | None = None,
        ) -> dict:
            _log(f"topic_hash={hash(topic)} port={mcp_settings.port} request_id={request_id}")
            await self.ensure_registered()
            model = await self.generate_content_structure_skill(topic)
            return transportify(model)

        @MCPTool.get_mcp(self).tool(
            name=f"{self.tool_mcp_path_prefix}.get_capabilities",
            title=f"{self.tool_mcp_path_prefix}.get_capabilities",
            description="Get the capabilities of the ContentStrategist tool.",
            tags={"tool", "capabilities", "info"},
        )
        async def get_capabilities() -> dict:
            await self.ensure_registered()
            return transportify(await self.get_capabilities())