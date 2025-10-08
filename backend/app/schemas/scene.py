from pydantic import BaseModel, Field
from typing import List, Optional


class Scene(BaseModel):
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
    props: List[str] = Field(default_factory=list)
    script_day: Optional[int] = None
    schedule_day_id: Optional[str] = None


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
