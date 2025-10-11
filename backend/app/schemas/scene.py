from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
from app.schemas.elements import SceneTag, SceneNote, SceneElement


class SceneCastAssignment(BaseModel):
    character_name: str
    actor_id: int | None = None
    actor_name: str | None = None
    union_status: str | None = None


class Scene(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    sequence_index: int = 0
    slugline: str
    page_eighths: int = Field(description="Number of eighths of a page (1/8 units).")
    page_decimal: float = Field(description="Decimal page length, e.g. 1.625.")
    estimated_minutes: float = Field(description="Estimated shooting time in minutes.")
    location: str
    day_night: str
    estimated_cost: float
    cast: List[str] = Field(default_factory=list)
    cast_details: List[SceneCastAssignment] = Field(default_factory=list)
    props: List[str] = Field(default_factory=list)
    script_day: Optional[int] = None
    schedule_day_id: Optional[str] = None
    synopsis: Optional[str] = None
    tags: List[SceneTag] = Field(default_factory=list)
    notes: List[SceneNote] = Field(default_factory=list)
    elements: List[SceneElement] = Field(default_factory=list)


class SceneUploadResponse(BaseModel):
    upload_id: str
    scenes: List[Scene]


class SceneIngestOptions(BaseModel):
    parse_only: bool = False


class PageLengthRequest(BaseModel):
    paragraphs: List[str]
    paragraph_types: List[str] | None = None


class PageLengthResponse(BaseModel):
    page_eighths: int
    page_decimal: float


class UploadSnapshot(BaseModel):
    upload_id: str
    original_filename: str
    total_scenes: int
    total_pages_decimal: float


class SceneUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: str | None = None
    cast: List[str] | None = None
    script_day: int | None = None

    @field_validator("script_day")
    @classmethod
    def validate_script_day(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if not 1 <= value <= 20:
            raise ValueError("script_day must be between 1 and 20.")
        return value


class BatchSceneAssignmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene_ids: List[str]
    script_day: int | None = None
    location: str | None = None

    @field_validator("scene_ids")
    @classmethod
    def validate_scene_ids(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("scene_ids must contain at least one scene id.")
        return value

    @field_validator("script_day")
    @classmethod
    def validate_batch_script_day(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if not 1 <= value <= 20:
            raise ValueError("script_day must be between 1 and 20.")
        return value
