from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import (
    ScriptUploadModel,
    SceneModel,
    SceneCastModel,
    ScenePropModel,
)
from ..schemas.scene import Scene
from ..services.fdx_parser import ParsedScene


async def create_script_upload(
    session: AsyncSession,
    upload_id: str,
    filename: str,
    mime_type: str,
    parsed_scenes: Iterable[ParsedScene],
) -> list[SceneModel]:
    scenes = []
    total_pages = 0.0

    upload = ScriptUploadModel(
        id=upload_id,
        original_filename=filename,
        mime_type=mime_type,
        uploaded_at=datetime.utcnow(),
    )
    session.add(upload)

    for parsed in parsed_scenes:
        scene_model = SceneModel(
            id=parsed.id,
            upload_id=upload_id,
            name=parsed.name,
            sequence_index=parsed.sequence_index,
            slugline=parsed.slugline,
            page_eighths=parsed.page_eighths,
            page_decimal=parsed.page_decimal,
            estimated_minutes=parsed.estimated_minutes,
            location=parsed.location,
            day_night=parsed.day_night,
            estimated_cost=parsed.estimated_cost,
        )
        for cast_name in parsed.cast:
            scene_model.cast_members.append(SceneCastModel(performer_name=cast_name))
        for prop_name in parsed.props:
            scene_model.props_used.append(ScenePropModel(prop_name=prop_name))
        session.add(scene_model)
        scenes.append(scene_model)
        total_pages += parsed.page_decimal

    upload.total_scenes = len(scenes)
    upload.total_pages_decimal = total_pages

    await session.commit()
    await session.refresh(upload)

    return scenes


async def list_scenes_for_upload(session: AsyncSession, upload_id: str) -> list[SceneModel]:
    result = await session.execute(
        select(SceneModel)
        .where(SceneModel.upload_id == upload_id)
        .order_by(SceneModel.sequence_index.asc())
    )
    return list(result.scalars().unique().all())


async def get_latest_upload(session: AsyncSession) -> ScriptUploadModel | None:
    result = await session.execute(
        select(ScriptUploadModel).order_by(ScriptUploadModel.uploaded_at.desc()).limit(1)
    )
    return result.scalars().first()
