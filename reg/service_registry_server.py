import os
from typing import Any

from fastmcp import FastMCP
from pydantic import Field
from python_a2a import A2AServer, run_server, skill, agent

from core.builders.cmd_args_parser_builder import build_cmd_args_parser, Argument
from core.config_env import config_env
from core.foundation.models.tools_model import ToolsModel
from core.utils.async_lib import start_background_processes, start_servers, continuous_process
from core.utils.encoders.transport_encoder import transportify
from core.utils.run_blocking import run_blocking


@agent(
    name="ServiceRegistry Tool",
    version="1.0.0",
    description="The central service repository is the centralised place for discovering tools available in for providing service. This tool exposes functions for Clients and Agents to discover and interact with tools to plan a workflow.",
    tags=["tool", "content", "structure", "outline", "topic", "strategy"],
)
class ServiceRegistryServer(A2AServer):
    mcp_server: FastMCP
    name: str
    host: str
    mcp_port: int
    a2a_port: int
    tools_registry: dict[str, ToolsModel] = {}
    def __init__(self, host: str, mcp_port: int, a2a_port:int, name="Service Registry"):
        super().__init__()
        self.mcp_server = FastMCP(
            name= name,
            version="1.0.0",
            instructions=" The central service repository is the centralised place for discovering tools available in for providing service. This tool exposes functions for Clients and Agents to discover and interact with tools to plan a workflow.")
        self.name = name
        self._host = host
        self._mcp_port = mcp_port
        self._a2a_port = a2a_port
        self.register_mcp_tools()
        run_blocking(self.self_register())

    async def self_register(self):
        self._add_tool_to_registry(
            ToolsModel(
                registry_id="service_registry",
                name=self.name,
                title="Service Registry",
                version="1.0.0",
                description="Centralized service repository for discovering and managing tools.",
                endpoint=f"http://{self._host}:{self._a2a_port}",
                capabilities= await self._get_capabilities(),
                tags=["tool", "registry", "service", "discovery", "workflow"],
                guidelines="Use this tool to discover and manage available services and tools. This is your bible for planning workflows.",
                metadata={"version": "1.0.0", "protocol": "A2A"}
            )
        )

    def _add_tool_to_registry(self, tool: ToolsModel) -> None:
        self.tools_registry[tool.registry_id] = tool

    def _list_tools(self) -> dict[str, ToolsModel]:
        return {rid: transportify(tool) for rid, tool in self.tools_registry.items()}

    def _get_tool(self, registry_id: str) -> ToolsModel | None:
        return transportify(self.tools_registry.get(registry_id, None))

    async def _get_capabilities(self) -> dict[str, Any]:
        return {
            "a2a_capability": self.agent_card.to_dict(),
            "mcp_capability": {
                "name": self.mcp_server.name,
                "host": self._host,
                "port": self._mcp_port,
                "tools": transportify(await self.mcp_server.get_tools()),
                "resources": transportify(await self.mcp_server.get_resources()),
                "prompts": transportify(await self.mcp_server.get_prompts()),
            }
        }

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
        tags={"tool", "registry", "get", "fetch tool", "service", "discovery"}
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

    def register_mcp_tools(self):
        @self.mcp_server.tool(
            name="service_registry.list_tools",
            title="List Registered Tools",
            description="List all tools currently registered in the service registry.",
            tags={"tool", "registry", "list", "service", "discovery"},
        )
        def list_tools() -> dict[str, ToolsModel]:
            return self._list_tools()

        @self.mcp_server.tool(
            name="service_registry.add_tool_to_registry",
            title="Add Tool to Registry",
            description="Add a new tool to the service registry.",
            tags={"tool", "registry", "add", "service", "discovery"},
            output_schema=None,
        )
        def add_tool_to_registry(tool: ToolsModel) -> None:
            self._add_tool_to_registry(tool)

        @self.mcp_server.tool(
            name="service_registry.get_tool",
            title="Get Tool by registry_id",
            description="Retrieve a tool's details by its registry id from the service registry.",
            tags={"tool", "registry", "get", "service", "discovery"},
            output_schema=ToolsModel.model_json_schema(),
        )
        def get_tool(registry_id: str = Field(description="Registry ID of the tool")) -> ToolsModel | None:
            return self._get_tool(registry_id)

        @self.mcp_server.tool(
            name="service_registry.get_capabilities",
            title="Get Capabilities",
            description="Get the capabilities of the Service Registry tool.",
            tags={"tool", "capabilities", "info"},
            output_schema=None
        )
        async def get_capabilities() -> dict:
            return await self._get_capabilities()

        @self.mcp_server.custom_route("/mcp/registry/add", methods=["POST"])
        async def register_tool_route(tool: ToolsModel) -> dict:
            self._add_tool_to_registry(tool)
            return {"status": "success", "message": f"Tool {tool.name} registered successfully."}

        @self.mcp_server.custom_route("/mcp/registry/get/{registry_id}", methods=["GET"])
        async def lookup_tool_route(registry_id: str) -> dict | None:
            tool = self._get_tool(registry_id)
            if tool:
                return tool.model_dump()
            return {"status": "error", "message": f"Tool with registry_id {registry_id} not found."}

        @self.mcp_server.custom_route("/mcp/registry/get/all", methods=["GET"])
        async def list_tools_route() -> dict[str, ToolsModel]:
           return self._list_tools()


    @start_servers()
    def setup_a2a_server(self) -> list[dict]:
        server_configs = [{
            'name': f"ServiceRegistry_A2A_{self.__class__.__name__}_{self._a2a_port}",
            'func': self.run_a2a_server,
            # 'args': (self._host, self._a2a_port)
        }]
        return server_configs

    @continuous_process
    def run_a2a_server(self):
        self.agent_card.url = f"http://{self._host}:{self._a2a_port}"
        run_server(self, host=self._host, port=self._a2a_port)

    @start_background_processes()
    def run_registry(self):
        self.setup_a2a_server()
        self.mcp_server.run(transport="http", host=self._host, port=self._mcp_port)


if __name__ == "__main__":
    config_env()
    arg_parser = build_cmd_args_parser("Launches Service Registry Server", [
        Argument(name="host", type=str, help="Host to run the server on", default=None),
        Argument(name="port", type=int, help="Port to run the server on", default=None),
        Argument(name="debug", type=bool, help="Enable debug mode", default=False),
    ])

    args = arg_parser.parse_args()

    env_host = args.host if args.host else os.getenv("SERVICE_REGISTRY_HOST", "127.0.0.1")
    env_port = args.port if args.port else int(os.getenv("SERVICE_REGISTRY_PORT", 7000))

    print("HOST", args.host, os.getenv("SERVICE_REGISTRY_HOST"),  env_host)
    print("PORT", args.port, os.getenv("SERVICE_REGISTRY_PORT"),  env_port)

    server = ServiceRegistryServer(
        host=env_host,
        mcp_port=env_port,
        a2a_port=env_port+10,
        name="Service Registry"
    )

    server.run_registry()