from core.config_env import config_env
from server.server import Server


def main():
    content_mcp_server = Server()
    content_mcp_server.register_tools()
    content_mcp_server.run()


if __name__ == "__main__":
    config_env()
    main()