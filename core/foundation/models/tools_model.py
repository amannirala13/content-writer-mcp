import uuid
from enum import Enum
from typing import Any

from pydantic import Field

from core.foundation.models.strict_mode import StrictModel

class ToolTypeEnum(Enum):
    MCP = "MCP"
    LLM = "LLM"
    A2A = "A2A"
    Other = "Other"

class SupportedProtocolsEnum(Enum):
    HTTP = "http"
    HTTPS = "https"
    WebSocket = "ws"
    gRPC = "grpc"
    MCP = "mcp"
    A2A = "a2a"
    Other = "other"

class ToolsModel(StrictModel):
    registry_id: str = Field(description="Unique identifier for the tool", default_factory=  lambda _ : uuid.uuid4().hex)
    name: str = Field(description="Name of the tool", default="")
    title: str = Field(description="Title of the tool", default="")
    description: str = Field(description="Description of the tool", default="")
    endpoint: str = Field(description="Endpoint of the tool", default="")
    protocol: SupportedProtocolsEnum = Field(description="Protocol used by the tool", default=SupportedProtocolsEnum.Other)
    capabilities: Any = Field(description="Capabilities of the tool", default={})
    tool_type: ToolTypeEnum = Field(description="Type of the tool", default=ToolTypeEnum.Other)
    version: str = Field(description="Version of the tool", default="1.0.0")
    guidelines: str = Field(description="Guidelines for using the tool", default="")
    metadata: dict = Field(description="Metadata of the tool", default={})
    tags: list[str] = Field(description="Tags associated with the tool", default=[])

