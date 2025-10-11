from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class SceneTag(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scene_id: str
    tag: str
    created_at: datetime


class SceneNote(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scene_id: str
    note_text: str
    note_type: str = "GENERAL"
    created_at: datetime
    updated_at: datetime


class ElementCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_name: str
    display_order: int = 0
    description: Optional[str] = None
    color: str = "#808080"


class SceneElement(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scene_id: str
    category_id: int
    element_name: str
    description: Optional[str] = None
    quantity: int = 1
    notes: Optional[str] = None
    is_critical: bool = False
    created_at: datetime
    updated_at: datetime

class SceneElementCreate(BaseModel):
    scene_id: str
    category_id: int
    element_name: str
    description: Optional[str] = None
    quantity: int = 1
    notes: Optional[str] = None
    is_critical: bool = False