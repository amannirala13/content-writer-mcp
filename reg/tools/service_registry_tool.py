from docutils.nodes import description
from mcp.server import FastMCP
from pydantic import Field
from python_a2a import skill, agent

from core.foundation.models.tools_model import ToolsModel
from core.foundation.tools import A2ATool, MCPTool


@agent(
    name="ServiceRegistry Tool",
    version="1.0.0",
    description="The central service repository is the centralised place for discovering tools available in for providing service. This tool exposes functions for Clients and Agents to discover and interact with tools to plan a workflow.",
    tags=["tool", "content", "structure", "outline", "topic", "strategy"],
)
class ServiceRegistryTool(A2ATool, MCPTool):
    tools_registry: dict[str, ToolsModel] = {}

    def __init__(self, mcp_server: FastMCP, **kwargs):
        A2ATool.__init__(self, mcp_server, **kwargs)
        MCPTool.__init__(self, mcp_server)
        self.tool_mcp_path_prefix = "service_registry"

    def _add_tool_to_registry(self, tool: ToolsModel) -> None:
        self.tools_registry[tool.registry_id] = tool

    def _list_tools(self) -> dict[str, ToolsModel]:
        return self.tools_registry

    def _get_tool(self, registry_id: str) -> ToolsModel | None:
        return self.tools_registry.get(registry_id, None)

    @skill(
        name="add_tool_to_registry",
        description="Add a new tool to the service registry.",
        tags={"tool", "registry", "add", "service", "discovery"},
    )
    def add_tool_to_registry_skill(self, tool: ToolsModel) -> None:
        """Skill to add a tool to the registry."""
        self._add_tool_to_registry(tool)

    @skill(
        name="list_tools",
        description="List all tools currently registered in the service registry.",
        tags={"tool", "registry", "list", "service", "discovery"},
    )
    def list_tools_skill(self) -> dict[str, ToolsModel]:
        """Skill to list all registered tools."""
        return self._list_tools()

    @skill(
        name="get_tool_skill",
        description=" Get a tool currently registered in the service registry using registry_id",
        tags={"tool", "registry", "get", "fetch tool" ,"service", "discovery"}
    )
    def get_tool_skill(self, registry_id: str) -> ToolsModel | None:
        """Skill to get a tool by its registry ID."""
        return self._get_tool(registry_id)

    @skill(
        name="get_capabilities_skill",
        description="Get the capabilities of the Service registry tool.",
        tags=["tool", "capabilities", "info"],
    )
    async def get_capabilities_skill(self) -> dict:
        """Skill to get the capabilities of the Service Registry tool."""
        return await self._get_capabilities()


    async def _get_capabilities(self) -> dict:
        return {
            "mcp_capability": await MCPTool._get_capabilities(self),
            "a2a_capability": await A2ATool._get_capabilities(self),
        }


    def register_tool(self) -> None:
        @self.get_mcp().tool(
        name=f"{self.tool_mcp_path_prefix}.add_tool_to_registry",
        title="Add Tool to Registry",
        description="Add a new tool to the service registry.",
        tags={"tool", "registry", "add", "service", "discovery"},
        output_schema=None,
        )
        def add_tool_to_registry(tool: ToolsModel) -> None:
            self._add_tool_to_registry(tool)

        @MCPTool.get_mcp(self).tool(
            name=f"{self.tool_mcp_path_prefix}.list_tools",
            title="List Registered Tools",
            description="List all tools currently registered in the service registry.",
            tags={"tool", "registry", "list", "service", "discovery"},
        )
        def list_tools() -> dict[str, ToolsModel]:
            return self._list_tools()

        @MCPTool.get_mcp(self).tool(
            name=f"{self.tool_mcp_path_prefix}.get_tool",
            title="Get Tool by Name",
            description="Retrieve a tool's details by its registry id from the service registry.",
            tags={"tool", "registry", "get", "service", "discovery"},
            output_schema=ToolsModel.model_json_schema(),
        )
        def get_tool(registry_id: str = Field(description="Registry ID of the tool")) -> ToolsModel | None:
            return self._get_tool(registry_id)

        @MCPTool.get_mcp(self).tool(
            name=f"{self.tool_mcp_path_prefix}.get_capabilities",
            title="Get Capabilities",
            description="Get the capabilities of the Service Registry tool.",
            tags={"tool", "capabilities", "info"},
        )
        async def get_capabilities() -> dict:
            return await self._get_capabilities()


        @MCPTool.get_mcp(self).custom_route("/mcp/register/tool", methods=["POST"])
        async def register_tool_route(tool: ToolsModel) -> dict:
            self._add_tool_to_registry(tool)
            return {"status": "success", "message": f"Tool {tool.name} registered successfully."}

        @MCPTool.get_mcp(self).custom_route("/mcp/lookup/tool/{registry_id}", methods=["GET"])
        async def lookup_tool_route(registry_id: str) -> dict | None:
            tool = self._get_tool(registry_id)
            if tool:
                return tool.model_dump()
            return {"status": "error", "message": f"Tool with registry_id {registry_id} not found."}

        @MCPTool.get_mcp(self).custom_route("/mcp/list/tools", methods=["GET"])
        async def list_tools_route() -> dict[str, dict]:
            return {rid: tool.model_dump() for rid, tool in self._list_tools().items()}
