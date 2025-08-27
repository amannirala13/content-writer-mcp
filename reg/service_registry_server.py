import os

from pydantic import Field

from core.builders.cmd_args_parser_builder import build_cmd_args_parser, Argument
from core.config_env import config_env
from core.foundation.models.tools_model import ToolsModel
from core.foundation.base_server import BaseServer
from core.foundation.tools import A2ATool
from reg.tools.service_registry_tool import ServiceRegistryTool


class ServiceRegistryServer(BaseServer):

    def __init__(self, host: str, port: int, name="Service Registry"):
        super().__init__(host, port, name)
        registry_tool: ServiceRegistryTool = ServiceRegistryTool(mcp_server=self.get())

        self.load_default_tools([registry_tool])
        self.register_tools()



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
        port=env_port,
        name="Service Registry"
    )

    server.run()