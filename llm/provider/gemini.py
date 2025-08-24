"""
@author: Shashank Kothari
@date: 2025-8-24
@description: This module provides an asynchronous client for interacting with Google's Gemini language models.
             It extends the LLMAgent abstract base class and implements methods for generating text
             based on prompts and message histories.
"""

import os
import google.generativeai as genai
from llm.llm_agent import LLMAgent


class GeminiClient(LLMAgent):
    """
    A client for interacting with Gemini's language models asynchronously.
    This class extends the LLMAgent abstract base class and provides implementations
    for generating text based on prompts.

    :param api_key_flag: The environment variable name where the Gemini API key is stored.
                         Defaults to "GEMINI_API_KEY".
    :param system_behavior: An optional system behavior prompt to guide the model's responses.
    :param config: A dictionary of configuration options for the Gemini API (e.g., model).

    :raises ValueError: If the API key is not found in the environment variables.
    :example:
        client = GeminiClient(
            api_key_flag="MY_GEMINI_API_KEY",
            system_behavior="You are a helpful assistant.",
            config={"model": "gemini-pro"}
        )
        response = await client.generate_text("Hello, how are you?")
    """

    def __init__(
        self,
        api_key_flag: str = None,
        system_behavior: str = None,
        config: dict = None,
    ):
        """
        Initialize the GeminiClient with optional API key flag, system behavior, and configuration.
        """
        super().__init__(config=config)

        api_key = os.getenv(api_key_flag if api_key_flag else "GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key not found in environment variables.")

        genai.configure(api_key=api_key)

        self._model_name = (config or self.get_default_config())["model"]
        self._model = genai.GenerativeModel(self._model_name)
        self._system_behavior = system_behavior

    def get_default_config(self) -> dict:
        """
        Get the default configuration for the Gemini API client.
        :return: A dictionary containing the default configuration settings.
        """
        return {
            "model": "gemini-pro",
        }

    def define_system_behavior(self, system_behavior: str) -> None:
        """
        Define the system behavior prompt.
        :param system_behavior: The prompt used to guide the assistant's behavior.
        """
        self._system_behavior = system_behavior

    async def generate_text(self, prompt: str, config: dict = None) -> str:
        """
        Generate text based on a single prompt.
        :param prompt: The input prompt to generate text from.
        :param config: Optional override config (not widely used in Gemini yet).
        :return: The generated text from the model.
        """
        full_prompt = self._prepend_system_behavior(prompt)
        response = await self._model.generate_content_async(full_prompt)
        return response.text

    async def generate_text_with_messages(
        self, messages: list, config: dict = None
    ) -> str:
        """
        Generate text based on a list of messages.
        :param messages: A list of message dicts with 'role' and 'content'.
        :param config: Optional override config.
        :return: The generated text from the model.
        """
        history = []
        if self._system_behavior:
            history.append(self.system_message(self._system_behavior))
        history.extend(messages)

        # Gemini expects raw text prompts or chat-style history; we'll convert accordingly.
        chat_session = self._model.start_chat(history=history)
        response = await chat_session.send_message_async(messages[-1]["content"])
        return response.text

    def get_client(self):
        """
        Get the underlying Gemini GenerativeModel instance.
        :return: The GenerativeModel instance.
        """
        return self._model

    def _prepend_system_behavior(self, prompt: str) -> str:
        """
        Prepend system behavior to prompt if defined.
        """
        return (
            f"{self._system_behavior}\n\n{prompt}" if self._system_behavior else prompt
        )

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
