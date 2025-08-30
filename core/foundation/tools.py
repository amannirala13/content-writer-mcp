from __future__ import annotations
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from random import random
from typing import Dict, Optional

from fastmcp import FastMCP, Client
from fastmcp.client import StreamableHttpTransport
from python_a2a import A2AServer, run_server

from core.foundation.models.tools_model import ToolsModel
from core.utils.runtime_utils.async_lib import continuous_process
from fastmcp import settings as mcp_settings


class MCPTool(ABC):
    def __init__(self, mcp_server: FastMCP):
        self._mcp = mcp_server
        self.tool_mcp_path_prefix = f"{self._mcp.name}.{self.__class__.__name__}"

    def get_mcp(self) -> FastMCP:
        return self._mcp

    async def _get_capabilities(self) -> dict:
        mcp = self.get_mcp()
        return {
            "name": mcp.name,
            "version": mcp.version,
            "tools": [t for t in (await mcp.get_tools())],
            "resources": [r for r in await mcp.get_resources()],
            "prompts": [p for p in await mcp.get_prompts()],
        }

    async def get_capabilities(self) -> dict:
        return await self._get_capabilities()

    @abstractmethod
    def register_tool(self) -> None:
        ...


class A2ATool(A2AServer, ABC):
    def __init__(self, mcp_server: FastMCP, **kwargs):
        super().__init__(**kwargs)

    async def _get_capabilities(self) -> dict:
        return self.agent_card.to_dict()

    async def get_capabilities(self) -> dict:
        return await self._get_capabilities()

    @continuous_process
    def run(self, host: str, port: int, **kwargs):
        self.agent_card.url = f"http://{host}:{port}"
        run_server(self, host, port, **kwargs)


class LookupServiceRegistry:
    def __init__(self, mcp_server: FastMCP, registry_url: str):
        self.mcp = mcp_server
        self._registry_url: str = registry_url

    @asynccontextmanager
    async def _client(self):
        async with Client(StreamableHttpTransport(url=self._registry_url)) as c:
            yield c

    async def _get_capabilities(self) -> dict:
        async with self._client() as client:
            result = await client.call_tool("service_registry.get_capabilities")
            return result.structured_content

    async def get_capabilities(self) -> dict:
        return await self._get_capabilities()

    async def lookup_service(self, registry_id: str) -> Optional[ToolsModel]:
        async with self._client() as client:
            result = await client.call_tool(
                "service_registry.get_tool",
                arguments={"registry_id": registry_id},
            )
            if result.structured_content is None:
                return None
            return ToolsModel.model_validate(result.structured_content)

    async def register_service(self, service: ToolsModel) -> None:
        async with self._client() as client:
            await client.call_tool(
                "service_registry.add_tool_to_registry",
                arguments={"tool": service.model_dump()},
            )

    async def list_services(self) -> Dict[str, ToolsModel]:
        async with self._client() as client:
            result = await client.call_tool("service_registry.list_tools")
            tools: Dict[str, ToolsModel] = {}
            for reg_id, item in result.structured_content.items():
                tools[reg_id] = ToolsModel.model_validate(item)
            return tools

'''
--------------------------------------------------------------
------------------ [ Registry Aware Mixin ] -------------------
--------------------------------------------------------------
'''

class RegistryAwareMixin(LookupServiceRegistry):
    """
    Reusable mixin that guarantees:
      - background retry registration with jitter
      - singleflight for concurrent callers
      - awaitable barrier ensure_registered on every public handler
    """

    def __init__(self, *args, **kwargs):
        # LookupServiceRegistry.__init__ must be called by subclass
        super().__init__(*args, **kwargs)
        self._reg_ok = False
        self._reg_event = asyncio.Event()
        self._reg_lock = asyncio.Lock()
        self._reg_task: Optional[asyncio.Task] = None

        # Registration is now disabled. An external process must register tools.
        # try to start registration on construction if a loop exists
        # try:
        #     loop = asyncio.get_running_loop()
        #     self._reg_task = loop.create_task(self._register_with_retries())
        # except RuntimeError:
        #     # no loop yet. first caller will trigger ensure_registered
        #     pass

    async def ensure_registered(self) -> None:
        if self._reg_ok:
            return
        async with self._reg_lock:
            if self._reg_ok:
                return
            if self._reg_task is None or self._reg_task.done():
                self._reg_task = asyncio.create_task(self._register_with_retries())
        await self._reg_event.wait()

    async def _register_with_retries(self) -> None:
        delay = 0.5
        while not self._reg_ok:
            try:
                await self._do_register_once()
                self._reg_ok = True
                self._reg_event.set()
                self._log("registry registration successful")
                return
            except Exception as e:
                self._log(f"registry registration failed: {e}")
                await asyncio.sleep(delay + random() * 0.25)
                delay = min(delay * 2, 10.0)

    async def _do_register_once(self) -> None:
        tool = await self.build_tools_model()
        await self.register_service(tool)

    async def build_tools_model(self) -> ToolsModel:
        """
        Subclasses must override if they want to customize name, tags, endpoint, etc.
        Default implementation builds from MCP server info.
        """
        mcp = self.mcp
        caps = await self.get_capabilities()
        return ToolsModel(
            name=mcp.name,
            version=mcp.version,
            description=f"Tool {mcp.name}",
            tags=["tool"],
            protocol=getattr(ToolsModel, "protocol", None) or None,  # override in subclass
            capabilities=caps,
            endpoint=f"http://{mcp_settings.host}:{mcp_settings.port}/mcp",
        )

    async def ping(self) -> str:
        return ("pong from " + self.__class__.__name__ + " at " +
                self.mcp.name +
                " { host:" +
                str(self.mcp.settings.host) +
                " port:" + str(mcp_settings.port) +
                " }")


    def _log(self, msg: str) -> None:
        print(f"[{self.__class__.__name__}] {msg}")
