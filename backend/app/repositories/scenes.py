from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable, Any, Dict
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db.models import (
    ScriptUploadModel,
    SceneModel,
    SceneCastModel,
    ScenePropModel,
    SceneTagModel,
    SceneElementModel,
    ElementCategoryModel,
    CharacterAssignmentModel,
    ActorCompensationModel,
    ScheduleDayOverrideModel,
)
from ..schemas.scene import Scene
from ..services.fdx_parser import ParsedScene

ACRONYM_WHITELIST = {
    "FBI",
    "CIA",
    "SWAT",
    "TV",
    "SUV",
    "NYPD",
    "LAPD",
    "DEA",
    "ATF",
}

STOP_WORDS = {
    "A", "AN", "THE", "OF", "IN", "ON", "AT", "FOR", "WITH", "BY",
    "IS", "AM", "ARE", "WAS", "WERE", "BE", "BEING", "BEEN",
    "AND", "BUT", "OR", "SO", "IF", "AS", "TO", "FROM"
}

LOCATION_SPLIT_PATTERN = re.compile(r"[/,&\-]+")


def _normalize_breakdown_label(value: str) -> str:
    tokens = value.strip().split()
    formatted: list[str] = []

    for token in tokens:
        cleaned = token.strip()
        if not cleaned:
            continue
        upper_token = cleaned.upper()
        if upper_token in STOP_WORDS:
            continue
        if upper_token in ACRONYM_WHITELIST:
            formatted.append(upper_token)
        elif len(cleaned) <= 3 and cleaned.isalpha():
            formatted.append(upper_token)
        else:
            formatted.append(cleaned.capitalize())

    return " ".join(formatted)


def _generate_auto_tags(parsed: ParsedScene) -> set[str]:
    tags: set[str] = set()
    slug_upper = parsed.slugline.upper()
    if slug_upper.startswith("INT/EXT"):
        tags.add("INT/EXT")
    elif slug_upper.startswith("INT"):
        tags.add("INT")
    elif slug_upper.startswith("EXT"):
        tags.add("EXT")

    day_tag = parsed.day_night.strip().upper() if parsed.day_night else ""
    if day_tag and day_tag not in {"", "OTHER"}:
        tags.add(day_tag)

    for location_part in LOCATION_SPLIT_PATTERN.split(parsed.location or ""):
        cleaned = location_part.strip()
        if len(cleaned) < 3:
            continue
        formatted = _normalize_breakdown_label(cleaned.title())
        if formatted:
            tags.add(formatted)

    # Filter out overly long tags to keep UI readable
    return {tag for tag in tags if 1 <= len(tag) <= 60}


async def create_script_upload(
    session: AsyncSession,
    upload_id: str,
    filename: str,
    mime_type: str,
    parsed_scenes: Iterable[ParsedScene],
) -> tuple[str, list[Scene]]:
    scenes = []
    total_pages = 0.0

    upload_uuid = UUID(upload_id)
    upload = ScriptUploadModel(
        id=upload_uuid,
        original_filename=filename,
        mime_type=mime_type,
        uploaded_at=datetime.utcnow(),
    )
    session.add(upload)

    category_result = await session.execute(select(ElementCategoryModel))
    category_lookup = {
        category.category_name: category
        for category in category_result.scalars()
    }

    for parsed in parsed_scenes:
        scene_model = SceneModel(
            id=UUID(parsed.id),
            upload_id=upload_uuid,
            name=parsed.name,
            sequence_index=parsed.sequence_index,
            slugline=parsed.slugline,
            page_eighths=parsed.page_eighths,
            page_decimal=parsed.page_decimal,
            estimated_minutes=parsed.estimated_minutes,
            location=parsed.location,
            day_night=parsed.day_night,
            estimated_cost=parsed.estimated_cost,
            synopsis=parsed.synopsis,
        )
        element_seen: set[tuple[int, str]] = set()

        for cast_name in parsed.cast:
            normalized_cast = _normalize_breakdown_label(cast_name.title())
            scene_model.cast_members.append(SceneCastModel(performer_name=normalized_cast))
            cast_category = category_lookup.get("Cast Members")
            if cast_category:
                element_key = (cast_category.id, normalized_cast.lower())
                if element_key not in element_seen:
                    scene_model.elements.append(
                        SceneElementModel(
                            category_id=cast_category.id,
                            category=cast_category,
                            element_name=normalized_cast,
                            quantity=1,
                        )
                    )
                    element_seen.add(element_key)

        for prop_name in sorted(set(parsed.props)):
            normalized_prop = _normalize_breakdown_label(prop_name)
            scene_model.props_used.append(ScenePropModel(prop_name=normalized_prop))

        for parsed_element in parsed.elements:
            category_model = category_lookup.get(parsed_element.category)
            if not category_model:
                continue
            normalized_name = _normalize_breakdown_label(parsed_element.name)
            element_key = (category_model.id, normalized_name.lower())
            if element_key in element_seen:
                continue
            scene_model.elements.append(
                SceneElementModel(
                    category_id=category_model.id,
                    category=category_model,
                    element_name=normalized_name,
                    quantity=max(1, parsed_element.quantity or 1),
                    description=parsed_element.description,
                    is_critical=parsed_element.is_critical,
                )
            )
            element_seen.add(element_key)

        auto_tags = _generate_auto_tags(parsed)
        for tag in auto_tags:
            scene_model.tags.append(SceneTagModel(tag=tag))

        session.add(scene_model)
        scenes.append(scene_model)
        total_pages += parsed.page_decimal

    upload.total_scenes = len(scenes)
    upload.total_pages_decimal = total_pages

    # Build Scene schemas before committing (while relationships are accessible)
    scene_schemas = []
    for scene in scenes:
        scene_schema = Scene(
            id=str(scene.id),
            name=scene.name,
            sequence_index=scene.sequence_index,
            slugline=scene.slugline,
            page_eighths=scene.page_eighths,
            page_decimal=scene.page_decimal,
            estimated_minutes=scene.estimated_minutes,
            location=scene.location,
            day_night=scene.day_night,
            estimated_cost=scene.estimated_cost,
            cast=[cast.performer_name for cast in scene.cast_members],
            props=[prop.prop_name for prop in scene.props_used],
            script_day=scene.script_day,
            schedule_day_id=str(scene.schedule_day_id) if scene.schedule_day_id else None,
            tags=[],  # Tags will be empty on initial upload, added later via UI
            notes=[],  # Notes will be empty on initial upload, added later via UI
            elements=[],  # Elements will be empty on initial upload, added later via UI
            synopsis=scene.synopsis,
        )
        scene_schemas.append(scene_schema)

    await session.commit()

    return upload_id, scene_schemas


async def list_scenes_for_upload(session: AsyncSession, upload_id: str | UUID) -> list[SceneModel]:
    upload_uuid = upload_id if isinstance(upload_id, UUID) else UUID(upload_id)
    result = await session.execute(
        select(SceneModel)
        .where(SceneModel.upload_id == upload_uuid)
        .options(
            selectinload(SceneModel.cast_members),
            selectinload(SceneModel.props_used),
            selectinload(SceneModel.tags),
            selectinload(SceneModel.notes),
            selectinload(SceneModel.elements).selectinload(SceneElementModel.category),
        )
        .order_by(SceneModel.sequence_index.asc())
    )
    return list(result.scalars().unique().all())


async def get_scene_by_id(session: AsyncSession, scene_id: str | UUID) -> SceneModel | None:
    scene_uuid = scene_id if isinstance(scene_id, UUID) else UUID(scene_id)
    result = await session.execute(
        select(SceneModel)
        .where(SceneModel.id == scene_uuid)
        .options(
            selectinload(SceneModel.cast_members),
            selectinload(SceneModel.props_used),
            selectinload(SceneModel.tags),
            selectinload(SceneModel.notes),
            selectinload(SceneModel.elements).selectinload(SceneElementModel.category),
        )
    )
    return result.scalars().first()


async def get_latest_upload(session: AsyncSession) -> ScriptUploadModel | None:
    result = await session.execute(
        select(ScriptUploadModel).order_by(ScriptUploadModel.uploaded_at.desc()).limit(1)
    )
    return result.scalars().first()


async def update_scene_metadata(
    session: AsyncSession,
    scene_id: str,
    update_fields: Dict[str, Any],
) -> SceneModel | None:
    scene_uuid = UUID(scene_id)
    result = await session.execute(
        select(SceneModel)
        .where(SceneModel.id == scene_uuid)
        .options(
            selectinload(SceneModel.cast_members),
            selectinload(SceneModel.props_used),
            selectinload(SceneModel.tags),
            selectinload(SceneModel.notes),
            selectinload(SceneModel.elements).selectinload(SceneElementModel.category),
        )
    )
    scene = result.scalars().first()
    if not scene:
        return None

    if not update_fields:
        return scene

    if "location" in update_fields:
        scene.location = update_fields["location"]

    if "script_day" in update_fields:
        scene.script_day = update_fields["script_day"]

    if "cast" in update_fields:
        cast = update_fields["cast"] or []
        await session.execute(delete(SceneCastModel).where(SceneCastModel.scene_id == scene_uuid))
        scene.cast_members = [
            SceneCastModel(performer_name=name.strip())
            for name in cast
            if name.strip()
        ]

    await session.commit()
    await session.refresh(scene)
    return scene


async def update_scenes_batch(
    session: AsyncSession,
    scene_ids: list[str],
    update_fields: Dict[str, Any],
) -> list[SceneModel]:
    if not scene_ids or not update_fields:
        return []

    scene_uuids = [UUID(sid) for sid in scene_ids]
    result = await session.execute(
        select(SceneModel)
        .where(SceneModel.id.in_(scene_uuids))
        .options(
            selectinload(SceneModel.cast_members),
            selectinload(SceneModel.props_used),
            selectinload(SceneModel.tags),
            selectinload(SceneModel.notes),
            selectinload(SceneModel.elements),
        )
    )
    scenes = list(result.scalars().all())
    if not scenes:
        return []

    if "location" in update_fields:
        for scene in scenes:
            scene.location = update_fields["location"]

    if "script_day" in update_fields:
        for scene in scenes:
            scene.script_day = update_fields["script_day"]

    if "cast" in update_fields:
        cast = update_fields["cast"] or []
        await session.execute(delete(SceneCastModel).where(SceneCastModel.scene_id.in_(scene_uuids)))
        for scene in scenes:
            scene.cast_members = [
                SceneCastModel(performer_name=name.strip())
                for name in cast
                if name.strip()
            ]

    if "script_day" in update_fields and "location" in update_fields:
        target_day = update_fields["script_day"]
        target_location = update_fields["location"]
        if target_day is not None:
            upload_id = scenes[0].upload_id
            additional_result = await session.execute(
                select(SceneModel)
                .where(
                    SceneModel.upload_id == upload_id,
                    SceneModel.script_day == target_day,
                )
            )
            for other_scene in additional_result.scalars().all():
                other_scene.location = target_location

    await session.commit()

    for scene in scenes:
        await session.refresh(scene)

    return scenes


async def delete_scene(session: AsyncSession, scene_id: str) -> bool:
    result = await session.execute(
        select(SceneModel).where(SceneModel.id == UUID(scene_id))
    )
    scene = result.scalars().first()
    if not scene:
        return False
    await session.delete(scene)
    await session.commit()
    return True


async def get_character_assignment_lookup(
    session: AsyncSession,
    upload_id: str | UUID,
) -> dict[str, dict[str, object]]:
    """Return mapping of uppercase character names to assignment details."""
    upload_uuid = upload_id if isinstance(upload_id, UUID) else UUID(upload_id)
    result = await session.execute(
        select(
            CharacterAssignmentModel.character_name,
            CharacterAssignmentModel.actor_id,
            ActorCompensationModel.actor_name,
            ActorCompensationModel.union_status,
        )
        .select_from(CharacterAssignmentModel)
        .join(
            ActorCompensationModel,
            CharacterAssignmentModel.actor_id == ActorCompensationModel.id,
            isouter=True,
        )
        .where(CharacterAssignmentModel.upload_id == upload_uuid)
    )

    lookup: dict[str, dict[str, object]] = {}
    for character_name, actor_id, actor_name, union_status in result:
        key = (character_name or "").strip().upper()
        if not key:
            continue
        lookup[key] = {
            "actor_id": actor_id,
            "actor_name": actor_name,
            "union_status": union_status,
        }
    return lookup


async def get_schedule_day_overrides(
    session: AsyncSession,
    upload_id: str | UUID,
) -> dict[int, ScheduleDayOverrideModel]:
    upload_uuid = upload_id if isinstance(upload_id, UUID) else UUID(upload_id)
    result = await session.execute(
        select(ScheduleDayOverrideModel).where(ScheduleDayOverrideModel.upload_id == upload_uuid)
    )
    overrides = {}
    for override in result.scalars().all():
        overrides[override.script_day] = override
    return overrides


async def upsert_schedule_day_location(
    session: AsyncSession,
    upload_id: str | UUID,
    script_day: int,
    location: str | None,
) -> ScheduleDayOverrideModel | None:
    """Create, update, or delete a schedule day override."""
    upload_uuid = upload_id if isinstance(upload_id, UUID) else UUID(upload_id)
    result = await session.execute(
        select(ScheduleDayOverrideModel).where(
            ScheduleDayOverrideModel.upload_id == upload_uuid,
            ScheduleDayOverrideModel.script_day == script_day,
        )
    )
    override = result.scalars().first()

    normalized_location = (location or "").strip()

    if not normalized_location:
        if override:
            await session.delete(override)
            await session.commit()
        return None

    if not override:
        override = ScheduleDayOverrideModel(
            upload_id=upload_uuid,
            script_day=script_day,
            shooting_location=normalized_location,
        )
        session.add(override)
    else:
        override.shooting_location = normalized_location

    await session.commit()
    await session.refresh(override)
    return override
