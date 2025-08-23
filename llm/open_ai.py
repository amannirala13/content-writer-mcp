import os

from openai import AsyncOpenAI

class OpenAIClient:
    def __init__(
            self,
            api_key: str = os.getenv("OPENAI_API_KEY"),
            model: str = "gpt-3.5-turbo",
            max_tokens: int = 150,
            system_behavior: str = None):
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens
        self._system_behavior = OpenAIClient.system_message(system_behavior) if system_behavior is not None else None

    def define_system_behavior(self, system_behavior: str) -> None:
        self._system_behavior = OpenAIClient.system_message(system_behavior)

    async def generate_text(self, prompt: str, model: str, max_tokens: int) -> str:
        response = await self._client.chat.completions.create(
            model= self._model if model is None else model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self._max_tokens if max_tokens is None else max_tokens,
        )
        return response.choices[0].message.content

    async def generate_text_with_messages(self, messages: list, model: str = None, max_tokens: int = None) -> str:
        response = await self._client.chat.completions.create(
            model= self._model if model is None else model,
            messages=[self._system_behavior] + messages if self._system_behavior is not None else messages,
            max_tokens=self._max_tokens if max_tokens is None else max_tokens,
        )
        return response.choices[0].message.content

    def get_client(self) -> AsyncOpenAI:
        return self._client

    @staticmethod
    def system_message(system_prompt: str) -> dict:
        return {"role": "system", "content": system_prompt}

    @staticmethod
    def user_message(user_prompt: str) -> dict:
        return {"role": "user", "content": user_prompt}

    @staticmethod
    def assistant_message(assistant_prompt: str) -> dict:
        return {"role": "assistant", "content": assistant_prompt}