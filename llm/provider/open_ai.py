import os

from openai import AsyncOpenAI

from llm.llm_agent import LLMAgent


class OpenAIClient(LLMAgent):

    def __init__(
            self,
            config: dict = None,):
        super().__init__(config=config)

        self._client = AsyncOpenAI(api_key=self.get_config()["api_key"])
        self._model = self.get_config()["model"]
        self._max_tokens = self.get_config()["max_tokens"]
        self._system_behavior = OpenAIClient.system_message( self.get_config()["system_behaviour"] ) if self.get_config().get("system_behaviour") else None

    def get_default_config(self) -> dict:
        return {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": "gpt-3.5-turbo",
            "max_tokens": 150,
            "system_behavior": None
        }

    def define_system_behavior(self, system_behavior: str) -> None:
        self._system_behavior = OpenAIClient.system_message(system_behavior)

    async def generate_text(self, prompt: str, config: dict = None) -> str:
        response = await self._client.chat.completions.create(
            model= config["model"] if config and "model" in config else self.get_default_config().get("model"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens= config["max_tokens"] if config and "max_tokens" in config else self.get_default_config().get("max_tokens"),
        )
        return response.choices[0].message.content

    async def generate_text_with_messages(self, messages: list, config: dict = None) -> str:
        response = await self._client.chat.completions.create(
            model= config["model"] if config and "model" in config else self.get_default_config().get("model"),
            messages= [self._system_behavior] + messages if self._system_behavior is not None else messages,
            max_tokens= config["max_tokens"] if config and "max_tokens" in config else self.get_default_config().get("max_tokens"),
        )
        print(response)
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