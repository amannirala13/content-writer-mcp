import os

from core.config_env import config_env
from server.mserver import MServer


def main(host: str, port: int):
    content_mcp_server = MServer(host, port)
    content_mcp_server.run()


if __name__ == "__main__":
    config_env()
    main(os.getenv("HOST"), int(os.getenv("PORT")))