from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SceneTag(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scene_id: UUID
    tag: str
    created_at: datetime


class SceneTagCreate(BaseModel):
    tag: str = Field(..., min_length=1, max_length=100)


class SceneNote(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scene_id: UUID
    note_text: str
    note_type: str = "GENERAL"
    created_at: datetime
    updated_at: datetime


class SceneNoteCreate(BaseModel):
    note_text: str = Field(..., min_length=1)
    note_type: str = Field(default="GENERAL", max_length=50)


class SceneNoteUpdate(BaseModel):
    note_text: Optional[str] = Field(default=None, min_length=1)
    note_type: Optional[str] = Field(default=None, max_length=50)


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
    scene_id: UUID
    category_id: int
    element_name: str
    description: Optional[str] = None
    quantity: int = 1
    notes: Optional[str] = None
    is_critical: bool = False
    category_name: Optional[str] = None
    category_color: Optional[str] = None
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


class SceneElementUpdate(BaseModel):
    category_id: Optional[int] = None
    element_name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    notes: Optional[str] = None
    is_critical: Optional[bool] = None


class MasterElement(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    upload_id: UUID
    category_id: int
    category_name: str
    category_color: str
    element_name: str
    description: Optional[str] = None
    total_scenes: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
