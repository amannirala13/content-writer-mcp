import os

from openai import AsyncOpenAI

from llm.llm_agent import LLMAgent


class OpenAIClient(LLMAgent):

    def __init__(
            self,
            api_key_flag: str = None,
            system_behavior: str = None,
            config: dict = None,):
        super().__init__(config=config)

        self._client = AsyncOpenAI(api_key=os.getenv(api_key_flag if api_key_flag else "OPENAI_API_KEY"))
        self._system_behavior = OpenAIClient.system_message( system_behavior ) if system_behavior else None

    def get_default_config(self) -> dict:
        return {
            "model": "gpt-5-nano",
        }

    def define_system_behavior(self, system_behavior: str) -> None:
        self._system_behavior = OpenAIClient.system_message(system_behavior)

    async def generate_text(self, prompt: str, config: dict = None) -> str:
        response = await self._client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            **(config if config else self.get_config())
        )
        return response.choices[0].message.content

    async def generate_text_with_messages(self, messages: list, config: dict = None) -> str:
        print("Calling with messages:", messages, " and config:", (config if config else self.get_config()))
        response = await self._client.chat.completions.create(
            messages= [self._system_behavior] + messages if self._system_behavior is not None else messages,
            **(config if config else self.get_config()))
        print("Response:", response)
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