from typing import List

from pydantic import BaseModel, Field

from .scene import Scene


class DayPlan(BaseModel):
    id: str
    name: str
    shooting_date: str | None = None
    total_cost: float = 0.0
    total_minutes: float = 0.0
    total_pages_decimal: float = 0.0
    location_summary: List[str] = Field(default_factory=list)
    cast_summary: List[str] = Field(default_factory=list)
    scenes: List[Scene] = Field(default_factory=list)


class AutoScheduleRequest(BaseModel):
    upload_id: str

