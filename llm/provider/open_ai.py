"""
@author: amannirala13
@date: 2025-8-23
@description: This module provides an asynchronous client for interacting with OpenAI's language models.
             It extends the LLMAgent abstract base class and implements methods for generating text
             based on prompts and message histories.
"""

import os
from openai import AsyncOpenAI
from llm.llm_agent import LLMAgent


class OpenAIClient(LLMAgent):
    """
    A client for interacting with OpenAI's language models asynchronously.
    This class extends the LLMAgent abstract base class and provides implementations
    for generating text based on prompts.

    :param api_key_flag: The environment variable name where the OpenAI API key is stored.
                            Defaults to "OPENAI_API_KEY".
    :param system_behavior: An optional system behavior prompt to guide the model's responses.
    :param config: A dictionary of configuration options for the OpenAI API (e.g., model, max_tokens).

    :raises ValueError: If the API key is not found in the environment variables.
    :example:
        client = OpenAIClient(
            api_key_flag="MY_OPENAI_API_KEY",
            system_behavior="You are a helpful assistant.",
            config={"model": "gpt-4", "max_tokens": 500}
        )
        response = await client.generate_text("Hello, how are you?")

    :return: The generated text from the model.
    """
    def __init__(
            self,
            api_key_flag: str = None,
            system_behavior: str = None,
            config: dict = None,):
        """
        Initialize the OpenAIClient with optional API key flag, system behavior, and configuration.
        :param api_key_flag:
        :param system_behavior:
        :param config:
        """
        super().__init__(config=config)

        self._client = AsyncOpenAI(api_key=os.getenv(api_key_flag if api_key_flag else "OPENAI_API_KEY"))
        self._system_behavior = OpenAIClient.system_message( system_behavior ) if system_behavior else None

    def get_default_config(self) -> dict:
        """
        Get the default configuration for the OpenAI API client.
        :return : A dictionary containing the default configuration settings.
        """
        return {
            "model": "gpt-5-nano",
        }

    def define_system_behavior(self, system_behavior: str) -> None:
        """
        Define the system behavior for the model's responses.
        :param system_behavior:
        :return: None
        """
        self._system_behavior = OpenAIClient.system_message(system_behavior)

    async def generate_text(self, prompt: str, config: dict = None) -> str:
        """
        Generate text based on a single prompt.
        :param prompt: The input prompt to generate text from.
        :param config: The configuration for the OpenAI API client.
        :return: The generated text from the model.
        """
        response = await self._client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            **(config if config else self.get_config())
        )
        return response.choices[0].message.content

    async def generate_text_with_messages(self, messages: list, config: dict = None) -> str:
        """
        Generate text based on a list of messages.
        :param messages: A list of message dictionaries, each containing 'role' and 'content'.
        :param config: The configuration for the OpenAI API client.
        :return: The generated text from the model.
        """
        response = await self._client.chat.completions.create(
            messages= [self._system_behavior] + messages if self._system_behavior is not None else messages,
            **(config if config else self.get_config()))
        return response.choices[0].message.content

    def get_client(self) -> AsyncOpenAI:
        """
        Get the underlying OpenAI API client instance.
        :return: The AsyncOpenAI client instance.
        """
        return self._client

    @staticmethod
    def system_message(system_prompt: str) -> dict:
        """
        Create a system message dictionary.
        :param system_prompt: The system prompt content.
        :return: A dictionary representing the system message.
        """
        return {"role": "system", "content": system_prompt}

    @staticmethod
    def user_message(user_prompt: str) -> dict:
        """
        Create a user message dictionary.
        :param user_prompt: The user prompt content.
        :return: A dictionary representing the user message.
        """
        return {"role": "user", "content": user_prompt}

    @staticmethod
    def assistant_message(assistant_prompt: str) -> dict:
        """
        Create an assistant message dictionary.
        :param assistant_prompt: The assistant prompt content.
        :return: A dictionary representing the assistant message.
        """
        return {"role": "assistant", "content": assistant_prompt}
