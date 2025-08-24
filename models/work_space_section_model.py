import uuid
from enum import Enum

from pydantic import BaseModel, Field

from models.strict_mode import StrictModel


class WorkSpaceSectionStateEnum(Enum):
    LOCKED = "LOCKED"
    REVIEW = "REVIEW"
    DRAFT = "DRAFT"
    EMPTY = "EMPTY"

class WorkSpaceSectionModel(StrictModel):
    id: uuid.UUID = Field(description="Unique identifier for the workspace section", default_factory=uuid.uuid4)
    workspace_id: uuid.UUID = Field(description="Identifier for the workspace this section belongs to")
    title: str = Field(description="Title of the workspace section", default="")
    description: str = Field(description="Description of the workspace section", default="")
    order: int = Field(description="Order of the section within the workspace", default=0)

    content: str = Field(description="Content of the workspace section", default="")

    seo_score: float = Field(description="SEO score of the section", default=0.0)
    seo_suggestions: list[str] = Field(description="SEO suggestions for the section", default=[])
    editor_score: float = Field(description="Editor score of the section", default=0.0)
    editor_suggestions: list[str] = Field(description="Editor suggestions for the section", default=[])
    planner_suggestions: list[str] = Field(description="Planner suggestions for the section", default=[])

    word_count: int = Field(description="Word count of the section", default=0)
    status:WorkSpaceSectionStateEnum = Field(description="Status of the section", default= WorkSpaceSectionStateEnum.EMPTY if not content else WorkSpaceSectionStateEnum.DRAFT)