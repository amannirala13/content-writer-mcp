from abc import ABC, abstractmethod

from fastmcp import FastMCP

class LLMAgent(ABC):
    def __init__(
            self,
            mcp_server: FastMCP = None,
            config: dict = None
    ):
        self._mcp_server: FastMCP = mcp_server
        self._config: dict = self.get_processed_config(config) if config else self.get_default_config()
        self._client: any = None

    @staticmethod
    @abstractmethod
    def get_default_config() -> dict:
        pass

    def get_processed_config(self, config: dict) -> dict:
        # over right default config fields with provided config fields
        processed_config = self.get_default_config().copy()
        if config:
            for key, value in config.items():
                processed_config[key] = value if value is not None else processed_config.get(key)
        return processed_config

    @abstractmethod
    def define_system_behavior(self, behavior: str) -> None:
       pass

    @abstractmethod
    async def generate_text(self, prompt: str, config: dict = None) -> str:
        pass

    @abstractmethod
    async def generate_text_with_messages(self, messages: list, config: dict = None) -> str:
        pass

    @staticmethod
    @abstractmethod
    def system_message(system_prompt: str) -> dict:
        pass

    @staticmethod
    @abstractmethod
    def user_message(user_prompt: str) -> dict:
        pass

    @staticmethod
    @abstractmethod
    def assistant_message(assistant_prompt: str) -> dict:
        pass

    def get_mcp(self) -> FastMCP:
        return self._mcp_server

    def get_config(self) -> dict:
        return self._config

    def get_client(self) -> any:
        return self._client
