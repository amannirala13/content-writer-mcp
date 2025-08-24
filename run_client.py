import asyncio
import os

from client.client import MyClient
from core.config_env import config_env


async def main(host: str = None, port: int = None):
    my_client = MyClient(f"http://{host}:{port}/mcp")
    await my_client.connect()
    tools = await my_client.list_tools()
    print(tools)

    structure = await my_client.call_tool(
        tool_name="generate_content_structure",
        topic="How to build a profitable tech startup in 2025?",
    )
    print(structure.content[0].text)

    result = await my_client.call_tool(
        tool_name="assign_author",
        topic=structure.content[0].text,
        authors=[
            "Alice - Expert in Economics",
            "Bob - Expert in Environmental Science",
            "Charlie - Expert in Sociology",
            "Diana - Expert in Political Science",
            "Eve - Expert in Technology and Startups",
            "Elvis - Expert in Entrepreneurship and Business Development",
        ],
    )
    print(result.structured_content)

    await my_client.disconnect()


if __name__ == "__main__":
    config_env()
    asyncio.run(main(os.getenv("HOST"), int(os.getenv("PORT"))))
