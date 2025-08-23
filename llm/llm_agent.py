"""
@author: amannirala13
@date: 2025-8-23
@description: This module defines an abstract base class for LLM agents.
             An LLM agent interacts with a language model to perform various tasks such as text generation,
             conversation handling, and system behavior definition.
             This class provides a common interface and structure for different LLM implementations.
"""

from abc import ABC, abstractmethod

from fastmcp import FastMCP

class LLMAgent(ABC):
    """
    Abstract base class for LLM agents.
    An LLM agent interacts with a language model to perform various tasks such as text generation,
    conversation handling, and system behavior definition.
    This class provides a common interface and structure for different LLM implementations.

    :param mcp_server: An instance of FastMCP to register tools and manage interactions.
    :param config: A dictionary of configuration options for the LLM (e.g., model
                     parameters, response format).

    :raises NotImplementedError: If any of the abstract methods are not implemented in a subclass.
    :example:
        class MyLLMAgent(LLMAgent):
            def get_default_config(self):
                return {"model": "my-model"}
            def define_system_behavior(self, behavior: str):
                pass
            async def generate_text(self, prompt: str, config: dict = None) -> str
                pass
            async def generate_text_with_messages(self, messages: list, config: dict = None)
                pass
            @staticmethod
            def system_message(system_prompt: str) -> dict:
                pass
            @staticmethod
            def user_message(user_prompt: str) -> dict:
                pass
            @staticmethod
            def assistant_message(assistant_prompt: str) -> dict:
                pass

        agent = MyLLMAgent(mcp_server=my_mcp, config={"model": "my-model"})
        agent.define_system_behavior("You are a friendly assistant.")
        response = await agent.generate_text("Hello, how are you?")
        response_with_messages = await agent.generate_text_with_messages(
            messages=[
                MyLLMAgent.system_message("You are a helpful assistant."),
                MyLLMAgent.user_message("Hello, how are you?")])

    :return: The generated text from the model.
    """
    def __init__(
            self,
            mcp_server: FastMCP = None,
            config: dict = None):
        """
        Initialize the LLMAgent with an MCP server and optional configuration.
        :param mcp_server: An instance of FastMCP to register tools and manage interactions.
        :param config: A dictionary of configuration options for the LLM.
        """
        self._mcp_server: FastMCP = mcp_server
        self._config: dict = self.get_processed_config(config) if config else self.get_default_config()
        self._client: any = None

    @staticmethod
    @abstractmethod
    def get_default_config() -> dict:
        """
        Get the default configuration for the LLM agent.
        :return: A dictionary containing the default configuration settings.
        """
        pass

    def get_processed_config(self, config: dict) -> dict:
        """
        Process the provided configuration by merging it with the default configuration.
        :return: A dictionary containing the processed configuration settings.
        :param config: A dictionary of configuration options to be processed.
        """
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
        """
        Generate text based on a single prompt.
        :param prompt: The input prompt to generate text from.
        :param config: The configuration for the LLM agent.
        :return: The generated text from the model.
        """
        pass

    @abstractmethod
    async def generate_text_with_messages(self, messages: list, config: dict = None) -> str:
        """
        Generate text based on a list of messages.
        :param messages: A list of message dictionaries, each containing 'role' and 'content'.
        :param config: The configuration for the LLM agent.
        :return: The generated text from the model.
        """
        pass

    @staticmethod
    @abstractmethod
    def system_message(system_prompt: str) -> dict:
        """
        Create a system message dictionary.
        :param system_prompt: The system prompt content.
        :return: A dictionary representing the system message.
        """
        pass

    @staticmethod
    @abstractmethod
    def user_message(user_prompt: str) -> dict:
        """
        Create a user message dictionary.
        :param user_prompt: The user prompt content.
        :return: A dictionary representing the user message.
        """
        pass

    @staticmethod
    @abstractmethod
    def assistant_message(assistant_prompt: str) -> dict:
        """
        Create an assistant message dictionary.
        :param assistant_prompt: The assistant prompt content.
        :return: A dictionary representing the assistant message.
        """
        pass

    def get_mcp(self) -> FastMCP:
        """
        Get the MCP server instance.
        :return: The FastMCP server instance.
        """
        return self._mcp_server

    def get_config(self) -> dict:
        """
        Get the current configuration of the LLM agent.
        :return: A dictionary containing the current configuration settings.
        """
        return self._config

    def get_client(self) -> any:
        """
        Get the underlying LLM client instance.
        :return: The LLM client instance.
        """
        return self._client
