from typing import Any

from pydantic import Field, field_validator

from core.foundation.models.strict_mode import StrictModel


class SubtopicModel(StrictModel):
    subtopic: str = Field(description="A specific subtopic to be covered in the content", default="")
    questions: list[str] = Field(description="List of questions related to the subtopic", default=[])
    headings: list[str] = Field(description="List of headings related to the subtopic", default=[])
    runtime: Any = Field(default=None, exclude=True)

class TopicStructureModel(StrictModel):
    topic: str = Field(description="The main topic of the content", default="")
    subtopics: list[SubtopicModel] = Field(description="List of subtopics under the main topic", default=[])
    runtime: Any = Field(default=None, exclude=True)

class ContentStructureModel(StrictModel):
    title: str = Field(description = "Title of the content ", default="")
    objective: str = Field(description = " The main objective of the content", default="")
    target_audience: str = Field(description = "The target audience for the content", default="")
    strategic_guidelines_for_ai_writer: str = Field(description="Strategic Guidelines for the AI writer to follow while creating the content", default="")
    keywords: list[str] = Field(description = "List of keywords to be included in the content", default=[])
    topics: list[TopicStructureModel] = Field(description = "List of main topics and their subtopics to be covered in the content", default=[])
    images_description: list[Any] = Field(description = "List of relevant images descriptions to be included in the content", default=[])
    charts_description: list[Any] = Field(description = "List of relevant charts descriptions to be included in the content", default=[])
    tables_description: list[Any] = Field(description = "List of relevant tables descriptions to be included in the content", default=[])
    code_snippets_description: list[Any] = Field(description = "List of relevant code snippets descriptions to be included in the content", default=[])
    additional_notes: str = Field(description = "Any additional notes or instructions for the content", default="")
    runtime: Any = Field(default=None, exclude=True)

    @classmethod
    @field_validator("tables_description", mode="before")
    def coerce_table_descriptions(cls, v):
        if isinstance(v, list):
            out = []
            for item in v:
                if isinstance(item, str):
                    out.append(item)
                elif isinstance(item, dict):
                    title = item.get("title") or "Table"
                    out.append(str(title))
                else:
                    out.append(str(item))
            return out
        return v