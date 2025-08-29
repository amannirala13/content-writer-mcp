"""
@author: ShashankKothari-exe
@date: 2025-8-23
@description: This module provides an asynchronous client for interacting with LM Studio's
             Granite model (ibm/granite-3.2-8b). It extends the LLMAgent abstract base class
             and implements methods for generating text based on prompts and message histories.
"""

import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from llm.llm_agent import LLMAgent


class LocalLMClient(LLMAgent):
    """
    A client for interacting with LM Studio's Granite model asynchronously.
    This class extends the LLMAgent abstract base class and provides implementations
    for generating text based on prompts.

    :param local_endpoint: Local LLM endpoint URL.
    :param system_behavior: Optional system behavior prompt to guide the model's responses.
    :param config: A dictionary of configuration options for the LM Studio API (e.g., model, max_tokens).

    :example:
        client = GraniteClient(
            system_behavior="You are a helpful assistant.",
            config={"model": "ibm/granite-3.2-8b", "max_tokens": 500}
        )
        response = await client.generate_text("Hello, how are you?")
    """

    def __init__(
        self,
        local_endpoint: str = None,
        system_behavior: str = None,
        config: dict = None,
    ):
        """
        Initialize the GraniteClient with optional API key flag, system behavior, and configuration.
        """
        super().__init__(config=config)

        # LM Studio local server uses an OpenAI-compatible API but does not require authentication.
        load_dotenv()
        self._client = AsyncOpenAI(
            base_url=os.getenv(
                local_endpoint if local_endpoint else "LOCAL_LLM_ENDPOINT"
            ),
        )

        self._system_behavior = (
            LocalLMClient.system_message(system_behavior) if system_behavior else None
        )

    def get_default_config(self) -> dict:
        """
        Get the default configuration for the Granite client.
        """
        return {
            "model": "ibm/granite-3.2-8b",
        }

    def define_system_behavior(self, system_behavior: str) -> None:
        """
        Define the system behavior for the model's responses.
        """
        self._system_behavior = LocalLMClient.system_message(system_behavior)

    async def generate_text(self, prompt: str, config: dict = None) -> str:
        """
        Generate text based on a single prompt.
        """
        response = await self._client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            **(config or self.get_config()),
        )
        return response.choices[0].message.content

    async def generate_text_with_messages(
        self, messages: list, config: dict = None
    ) -> str:
        """
        Generate text based on a list of messages.
        """
        response = await self._client.chat.completions.create(
            messages=[self._system_behavior] + messages
            if self._system_behavior
            else messages,
            **(config if config else self.get_config()),
        )
        return response.choices[0].message.content

    def get_client(self) -> AsyncOpenAI:
        """
        Get the underlying AsyncOpenAI client instance.
        """
        return self._client

    @staticmethod
    def system_message(system_prompt: str) -> dict:
        """
        Create a system message dictionary.
        """
        return {"role": "system", "content": system_prompt}

    @staticmethod
    def user_message(user_prompt: str) -> dict:
        """
        Create a user message dictionary.
        """
        return {"role": "user", "content": user_prompt}

    @staticmethod
    def assistant_message(assistant_prompt: str) -> dict:
        """
        Create an assistant message dictionary.
        """
        return {"role": "assistant", "content": assistant_prompt}
