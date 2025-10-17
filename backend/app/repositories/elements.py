from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db.models import (
    ElementCategoryModel,
    MasterElementModel,
    SceneElementModel,
    SceneModel,
    SceneNoteModel,
    SceneTagModel,
)
from ..schemas.elements import SceneElementCreate, SceneElementUpdate, SceneNoteUpdate


async def list_element_categories(session: AsyncSession) -> list[ElementCategoryModel]:
    result = await session.execute(
        select(ElementCategoryModel).order_by(ElementCategoryModel.display_order, ElementCategoryModel.id)
    )
    return list(result.scalars().all())


async def list_scene_elements(session: AsyncSession, scene_id: UUID) -> list[SceneElementModel]:
    result = await session.execute(
        select(SceneElementModel)
        .options(selectinload(SceneElementModel.category))
        .where(SceneElementModel.scene_id == scene_id)
        .order_by(SceneElementModel.id)
    )
    return list(result.scalars().all())


async def create_scene_element(session: AsyncSession, element: SceneElementCreate) -> SceneElementModel:
    db_element = SceneElementModel(**element.model_dump())
    session.add(db_element)
    await session.commit()
    await session.refresh(db_element)
    await session.refresh(db_element, attribute_names=["category"])
    return db_element


async def update_scene_element(
    session: AsyncSession,
    scene_id: UUID,
    element_id: int,
    payload: SceneElementUpdate,
) -> SceneElementModel | None:
    data = {key: value for key, value in payload.model_dump(exclude_unset=True).items()}

    if data:
        data["updated_at"] = datetime.utcnow()
        stmt = (
            update(SceneElementModel)
            .where(SceneElementModel.id == element_id, SceneElementModel.scene_id == scene_id)
            .values(**data)
            .returning(SceneElementModel.id)
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            await session.rollback()
            return None
        await session.commit()

    element = await session.get(
        SceneElementModel,
        element_id,
        options=(selectinload(SceneElementModel.category),),
    )
    return element if element and element.scene_id == scene_id else None


async def delete_scene_element(session: AsyncSession, scene_id: UUID, element_id: int) -> bool:
    stmt = delete(SceneElementModel).where(
        SceneElementModel.id == element_id,
        SceneElementModel.scene_id == scene_id,
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def list_scene_tags(session: AsyncSession, scene_id: UUID) -> list[SceneTagModel]:
    result = await session.execute(
        select(SceneTagModel)
        .where(SceneTagModel.scene_id == scene_id)
        .order_by(SceneTagModel.id)
    )
    return list(result.scalars().all())


async def create_scene_tag(session: AsyncSession, scene_id: UUID, tag: str) -> SceneTagModel:
    db_tag = SceneTagModel(scene_id=scene_id, tag=tag.strip())
    session.add(db_tag)
    await session.commit()
    await session.refresh(db_tag)
    return db_tag


async def delete_scene_tag(session: AsyncSession, scene_id: UUID, tag_id: int) -> bool:
    stmt = delete(SceneTagModel).where(
        SceneTagModel.id == tag_id,
        SceneTagModel.scene_id == scene_id,
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def list_scene_notes(session: AsyncSession, scene_id: UUID) -> list[SceneNoteModel]:
    result = await session.execute(
        select(SceneNoteModel)
        .where(SceneNoteModel.scene_id == scene_id)
        .order_by(SceneNoteModel.id)
    )
    return list(result.scalars().all())


async def create_scene_note(
    session: AsyncSession,
    scene_id: UUID,
    note_text: str,
    note_type: str,
) -> SceneNoteModel:
    db_note = SceneNoteModel(scene_id=scene_id, note_text=note_text.strip(), note_type=note_type.strip().upper())
    session.add(db_note)
    await session.commit()
    await session.refresh(db_note)
    return db_note


async def update_scene_note(
    session: AsyncSession,
    scene_id: UUID,
    note_id: int,
    payload: SceneNoteUpdate,
) -> SceneNoteModel | None:
    update_data = payload.model_dump(exclude_unset=True)
    values: dict[str, Any] = {}

    if "note_text" in update_data:
        values["note_text"] = update_data["note_text"].strip()
    if "note_type" in update_data and update_data["note_type"] is not None:
        values["note_type"] = update_data["note_type"].strip().upper()

    if values:
        values["updated_at"] = datetime.utcnow()
        stmt = (
            update(SceneNoteModel)
            .where(SceneNoteModel.id == note_id, SceneNoteModel.scene_id == scene_id)
            .values(**values)
            .returning(SceneNoteModel.id)
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            await session.rollback()
            return None
        await session.commit()

    note = await session.get(SceneNoteModel, note_id)
    return note if note and note.scene_id == scene_id else None


async def delete_scene_note(session: AsyncSession, scene_id: UUID, note_id: int) -> bool:
    stmt = delete(SceneNoteModel).where(
        SceneNoteModel.id == note_id,
        SceneNoteModel.scene_id == scene_id,
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def list_master_elements(
    session: AsyncSession,
    upload_id: UUID,
    category_id: int | None = None,
) -> list[MasterElementModel]:
    stmt = (
        select(MasterElementModel)
        .where(MasterElementModel.upload_id == upload_id)
        .options(selectinload(MasterElementModel.category))
        .order_by(MasterElementModel.category_id, MasterElementModel.element_name)
    )
    if category_id is not None:
        stmt = stmt.where(MasterElementModel.category_id == category_id)

    result = await session.execute(stmt)
    records = list(result.scalars().all())
    if records:
        return records

    fallback_stmt = (
        select(
            SceneElementModel.category_id.label("category_id"),
            ElementCategoryModel.category_name.label("category_name"),
            ElementCategoryModel.display_order.label("display_order"),
            ElementCategoryModel.color.label("category_color"),
            SceneElementModel.element_name.label("element_name"),
            func.count(SceneElementModel.id).label("total_scenes"),
        )
        .join(ElementCategoryModel, SceneElementModel.category_id == ElementCategoryModel.id)
        .join(SceneModel, SceneElementModel.scene_id == SceneModel.id)
        .where(SceneModel.upload_id == upload_id)
        .group_by(
            SceneElementModel.category_id,
            ElementCategoryModel.category_name,
            ElementCategoryModel.display_order,
            ElementCategoryModel.color,
            SceneElementModel.element_name,
        )
        .order_by(ElementCategoryModel.display_order, SceneElementModel.element_name)
    )
    if category_id is not None:
        fallback_stmt = fallback_stmt.where(SceneElementModel.category_id == category_id)

    fallback = await session.execute(fallback_stmt)
    aggregated: list[MasterElementModel] = []
    now = datetime.utcnow()
    for idx, row in enumerate(fallback.mappings().all(), start=1):
        synthetic = MasterElementModel(
            id=-idx,
            upload_id=upload_id,
            category_id=row["category_id"],
            element_name=row["element_name"],
            description=None,
            total_scenes=row["total_scenes"],
            notes=None,
            created_at=now,
            updated_at=now,
        )
        synthetic.category = ElementCategoryModel(
            id=row["category_id"],
            category_name=row["category_name"],
            display_order=row["display_order"] or 0,
            color=row["category_color"],
        )
        aggregated.append(synthetic)
    return aggregated
