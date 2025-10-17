from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from ..db.models import ElementCategoryModel, SceneElementModel, SceneModel
from ..schemas.breakdown import BreakdownSheet
from ..schemas.elements import SceneElement

CATEGORY_FIELD_MAP: Dict[str, str] = {
    "Cast": "cast_members",
    "Extras": "extras",
    "Props": "props",
    "Set Dressing": "set_dressing",
    "Wardrobe": "wardrobe",
    "Makeup & Hair": "makeup_hair",
    "Vehicles & Animals": "vehicles_animals",
    "Sound FX": "sound_fx",
    "Special Effects": "special_effects",
    "Stunts": "stunts",
}

NOTE_FIELD_MAP: Dict[str, str] = {
    "GENERAL": "general_notes",
    "CAMERA": "camera_notes",
    "LIGHTING": "lighting_notes",
    "PRODUCTION": "production_notes",
}


def _element_to_schema(element: SceneElementModel) -> SceneElement:
    category = element.category
    schema = SceneElement.model_validate(element, from_attributes=True)
    if category:
        schema = schema.model_copy(
            update={
                "category_name": category.category_name,
                "category_color": category.color,
            }
        )
    return schema


def _derive_int_ext(slugline: str | None) -> str:
    if not slugline:
        return ""
    first_token = slugline.split()[0]
    cleaned = first_token.rstrip(":.").upper()
    if cleaned in {"INT", "EXT", "INT/EXT"}:
        return cleaned
    return ""


def _ensure_category_loaded(element: SceneElementModel) -> None:
    if element.category is None:
        element.category = ElementCategoryModel(
            id=element.category_id,
            category_name="",
            display_order=0,
            color="#808080",
        )


def build_breakdown_sheet(scene: SceneModel) -> BreakdownSheet:
    element_groups: Dict[str, List[SceneElement]] = {
        field: [] for field in CATEGORY_FIELD_MAP.values()
    }

    for element in scene.elements:
        _ensure_category_loaded(element)
        category_name = element.category.category_name or "General"
        field_name = CATEGORY_FIELD_MAP.get(category_name, "props")
        element_groups.setdefault(field_name, []).append(_element_to_schema(element))

    if not element_groups["cast_members"] and scene.cast_members:
        fallback_category = ElementCategoryModel(
            id=0,
            category_name="Cast",
            display_order=0,
            color="#BFDBFE",
        )
        now = datetime.utcnow()
        for cast_member in scene.cast_members:
            synthetic_element = SceneElementModel(
                id=0,
                scene_id=scene.id,
                category_id=0,
                element_name=cast_member.performer_name,
                description=None,
                quantity=1,
                notes=None,
                is_critical=False,
                created_at=now,
                updated_at=now,
            )
            synthetic_element.category = fallback_category
            element_groups["cast_members"].append(_element_to_schema(synthetic_element))

    notes_map: Dict[str, List[str]] = {
        "general_notes": [],
        "camera_notes": [],
        "lighting_notes": [],
        "production_notes": [],
    }
    for note in scene.notes:
        note_type = (note.note_type or "GENERAL").upper()
        target_field = NOTE_FIELD_MAP.get(note_type, "general_notes")
        notes_map[target_field].append(note.note_text)

    return BreakdownSheet(
        scene_id=str(scene.id),
        scene_name=scene.name,
        scene_number=scene.name,
        slugline=scene.slugline,
        int_ext=_derive_int_ext(scene.slugline),
        day_night=scene.day_night,
        location=scene.location,
        script_day=scene.script_day,
        page_count=scene.page_decimal,
        estimated_minutes=scene.estimated_minutes,
        description=scene.synopsis or "",
        cast_members=element_groups["cast_members"],
        extras=element_groups["extras"],
        props=element_groups["props"],
        set_dressing=element_groups["set_dressing"],
        wardrobe=element_groups["wardrobe"],
        makeup_hair=element_groups["makeup_hair"],
        vehicles_animals=element_groups["vehicles_animals"],
        sound_fx=element_groups["sound_fx"],
        special_effects=element_groups["special_effects"],
        stunts=element_groups["stunts"],
        general_notes=notes_map["general_notes"],
        camera_notes=notes_map["camera_notes"],
        lighting_notes=notes_map["lighting_notes"],
        production_notes=notes_map["production_notes"],
        tags=[tag.tag for tag in scene.tags],
    )


def build_breakdown_sheets(scenes: List[SceneModel]) -> List[BreakdownSheet]:
    return [build_breakdown_sheet(scene) for scene in scenes]
