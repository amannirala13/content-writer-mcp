from fastmcp import FastMCP

from core.foundation.look_up_service_registry import LookupServiceRegistryMCPTool
from core.utils.async_lib import continuous_process, start_background_processes, print_process_status, start_servers
from core.foundation.tools import MCPTool, A2ATool


class BaseServer:
    def __init__(self, host: str, port: int, name: str = "MCP Server"):
        self._host: str = host
        self._port: int = port
        self._mcp_server: FastMCP = FastMCP(name)
        self._tools: list[MCPTool | A2ATool | LookupServiceRegistryMCPTool] = []
        self._resources = []
        self._prompts = []

        # Register system tools - capabilities, health check, etc.
        self.register_system_tools()


    def load_default_tools(self, tools: list[MCPTool | A2ATool | LookupServiceRegistryMCPTool]):
        #self._tools.append()
        self._tools.extend(tools)

    def register_tools(self):
        for tool in self._tools:
            tool.register_tool()

    def register_system_tools(self) -> None:
        @self._mcp_server.tool(
            title=f"get_capabilities",
            description="Get the capabilities of the MCP server and its tools",
            tags={"tool", "mcp", "capabilities"},
            name="get_capabilities")
        async def get_capabilities() -> dict:
            capabilities = {"tools": {}, "resources": {}, "prompts": {}}
            for tool in self._tools:
                capabilities["tools"][tool.__class__.__name__] = await tool.get_capabilities()

            # TODO: Add resources and prompts capabilities
            return capabilities

    @start_servers()
    def setup_a2a_servers(self) -> list[dict]:
        """Setup A2A servers to run in separate threads"""
        print("Setting up A2A tool servers...")

        server_configs = []
        port_offset = 0

        # TODO: Ensure no port conflicts. Assign ports dynamically if needed.
        for i, tool in enumerate(self._tools):
            if hasattr(tool, 'agent_card'):  # It's an A2A tool
                server_port = 5001 + port_offset

                # Create a server configuration
                server_configs.append({
                    'name': f"A2A_{tool.__class__.__name__}_{server_port}",
                    'func': tool.run,
                    'args': ("127.0.0.1", server_port)
                })

                print(f"Configured A2A server: {tool.__class__.__name__} on port {server_port}")
                port_offset += 10
        return server_configs

    #@continuous_process
    def health_monitor(self):
        """Monitor server health"""
        return f"Server {self._mcp_server.name} is healthy"

    @start_background_processes()
    def run(self):
        self.setup_a2a_servers()
        self._mcp_server.run(transport="http", host=self._host, port=self._port)

    def get(self) -> FastMCP:
        return self._mcp_server