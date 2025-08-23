from fastmcp import FastMCP

from llm.llm_agent import LLMAgent
from llm.provider.open_ai import OpenAIClient
from tools.tools import Tools


class GenerateContentStructure(Tools):
    def __init__(self, mcp_server: FastMCP):
        super().__init__(mcp_server)
        self._llm_client: LLMAgent = OpenAIClient(
            config = {"model": "gpt-5-nano",
                      "response_format": {"type": "json_object"}
                      },
            system_behavior='''
                        You are an expert content strategist. Extract the main objective from the given content.
                        Provide different topics and aspects of the objective if applicable.
                        Define relevant images, charts, tables, or code snippets that could be included to enhance the content if applicable.
                        Proved a clear structure of topics and subtopics to be discussed/included if applicable.
                        Respond in a concise manner.
                        
                        Format your response in the following JSON structure:
                        {
                        "title": "Main topic of the content",
                        "objective": "The main objective of the content",
                        "topics": [
                            {
                                "topic": "Topic 1",
                                    "sub_topics": ["Sub Topic 1.1", "Sub Topic 1.2", "Sub Topic 1.3", ..., "Sub Topic 1.x"],
                            },
                            {
                                "topic": "Topic 2",
                                    "sub_topics": ["Sub Topic 2.1", "Sub Topic 2.2", "Sub Topic 2.3", ..., "Sub Topic 2.y"],
                            },
                            .
                            .
                            .
                            {
                                "topic": "Topic N",
                                    "sub_topics": ["Sub Topic N.1", "Sub Topic N.2", "Sub Topic N.3", ..., "Sub Topic N.z"],
                            },
                            ]
                        }
                        
                        Ensure the JSON is properly formatted.
                                        '''
        )

    def register_tool(self) -> None:
        @self.get_mcp().tool()
        async def generate_content_structure(topic: str) -> str:
            return await self._llm_client.generate_text_with_messages(
                messages=[
                    OpenAIClient.user_message(
                        f"Analyze the following topic and extract its main objective along with relevant topics and subtopics:\n\n{topic}"
                    )
                ]
            )
