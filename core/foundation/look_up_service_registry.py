from __future__ import annotations

import asyncio
from typing import Any, Coroutine

from mcp.server import FastMCP
from python_a2a import agent, skill

from core.foundation.models.tools_model import ToolsModel
from core.foundation.tools import A2ATool, LookupServiceRegistry, MCPTool, RegistryAwareMixin


@agent(
    name="LookupServiceRegistry Tool",
    version="1.0.0",
    description="A tool to look up and interact with a service registry for discovering available tools, resources and prompts. This tool allows clients and agents to query the registry, retrieve tool details, and register new services.",
    tags=["tool", "service", "registry", "lookup", "discovery"],)
class LookupServiceRegistryMCPTool(A2ATool, MCPTool, RegistryAwareMixin):
    def __init__(self, mcp_server: FastMCP , registry_url: str):
        MCPTool.__init__(self, mcp_server)
        A2ATool.__init__(self, mcp_server=mcp_server)
        LookupServiceRegistry.__init__(self, mcp_server, registry_url)

    @skill(
        name="look_up_service",
        description="Retrieve a tool's/resource's/prompt's details by its registry id from the service registry.",
        tags={"tool", "registry", "get", "service", "discovery"},)
    async def look_up_service_skill(self, registry_id: str) -> ToolsModel | None:
        return await self.lookup_service(registry_id)

    @skill(
        name="list_service",
        description="List all tools currently registered in the service registry.",
        tags={"tool", "registry", "list", "service", "discovery"}
    )
    async def list_services_skill(self) -> dict[str, ToolsModel]:
        return await self.list_services()

    @skill(
        name="register_service",
        description="Add a new tool/resource/prompt to the service registry.",
        tags={"tool", "registry", "add", "service", "discovery"},
    )
    async def register_service_skill(self,service: ToolsModel) -> None:
        await self.register_service(service)

    @skill(
        name="get_capabilities",
        description="Get the capabilities of the Service Registry tool.",
        tags={"tool", "capabilities", "info"},
    )
    async def get_capabilities_skill(self) -> dict:
        return await self._get_capabilities()

    async def _get_capabilities(self) -> dict:
        return {
            "mcp_capability": await MCPTool._get_capabilities(self),
            "a2a_capability": await A2ATool._get_capabilities(self),
            "registry_capability": await LookupServiceRegistry._get_capabilities(self)
        }


    def register_tool(self) -> None:
            @MCPTool.get_mcp(self).tool(
                name=f"{self.tool_mcp_path_prefix}.look_up_service",
                title="Look for and fetch Tool/Resource/Prompt by Name",
                description="Retrieve a tool's details by its registry id from the service registry.",
                tags={"tool", "registry", "get", "service", "discovery"},
                output_schema=ToolsModel.model_json_schema(),
            )
            async def look_up_service(registry_id: str) -> ToolsModel| None:
                return await self.lookup_service(registry_id)

            @MCPTool.get_mcp(self).tool(
                name=f"{self.tool_mcp_path_prefix}.list_service",
                title="List Registered Tool/Resource/Prompt",
                description="List all tools currently registered in the service registry.",
                tags={"tool", "registry", "list", "service", "discovery"},
            )
            async def list_services() -> dict[str, ToolsModel] | None:
                return await self.list_services()

            @MCPTool.get_mcp(self).tool(
                name=f"{self.tool_mcp_path_prefix}.register_service",
                title="Add Tool/Resource/Prompt to Registry",
                description="Add a new tool to the service registry.",
                tags={"tool", "registry", "add", "service", "discovery"},
                output_schema=None,
            )
            async def register_service(service: ToolsModel) -> None:
                await self.register_service(service)

            @MCPTool.get_mcp(self).tool(
                name=f"{self.tool_mcp_path_prefix}.get_capabilities",
                title="Get Capabilities",
                description="Get the capabilities of the Service Registry tool.",
                tags={"tool", "capabilities", "info"},
            )
            async def get_capabilities() -> dict:
                return await self._get_capabilities()

