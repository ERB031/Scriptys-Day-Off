from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, Field

from .elements import SceneElement


class BreakdownSheet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scene_id: str
    scene_name: str
    scene_number: str
    slugline: str
    int_ext: str = ""
    day_night: str
    location: str
    script_day: int | None = None
    page_count: float
    estimated_minutes: float
    description: str = ""
    cast_members: List[SceneElement] = Field(default_factory=list)
    extras: List[SceneElement] = Field(default_factory=list)
    props: List[SceneElement] = Field(default_factory=list)
    set_dressing: List[SceneElement] = Field(default_factory=list)
    wardrobe: List[SceneElement] = Field(default_factory=list)
    makeup_hair: List[SceneElement] = Field(default_factory=list)
    vehicles_animals: List[SceneElement] = Field(default_factory=list)
    sound_fx: List[SceneElement] = Field(default_factory=list)
    special_effects: List[SceneElement] = Field(default_factory=list)
    stunts: List[SceneElement] = Field(default_factory=list)
    general_notes: List[str] = Field(default_factory=list)
    camera_notes: List[str] = Field(default_factory=list)
    lighting_notes: List[str] = Field(default_factory=list)
    production_notes: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
