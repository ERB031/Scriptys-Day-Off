"""Scene elements endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session
from ...repositories.elements import (
    create_scene_element,
    create_scene_note,
    create_scene_tag,
    delete_scene_element,
    delete_scene_note,
    delete_scene_tag,
    list_element_categories,
    list_master_elements,
    list_scene_elements,
    list_scene_notes,
    list_scene_tags,
    update_scene_element,
    update_scene_note,
)
from ...schemas.elements import (
    ElementCategory,
    MasterElement,
    SceneElement,
    SceneElementCreate,
    SceneElementUpdate,
    SceneNote,
    SceneNoteCreate,
    SceneNoteUpdate,
    SceneTag,
    SceneTagCreate,
)

router = APIRouter()


def _parse_uuid(value: str, name: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{name} must be a valid UUID.",
        ) from exc


def _element_to_schema(model) -> SceneElement:
    schema = SceneElement.model_validate(model, from_attributes=True)
    category = getattr(model, "category", None)
    if category:
        schema = schema.model_copy(
            update={
                "category_name": category.category_name,
                "category_color": category.color,
            }
        )
    return schema


def _master_element_to_schema(model) -> MasterElement:
    schema = MasterElement.model_validate(model, from_attributes=True)
    category = getattr(model, "category", None)
    if category:
        schema = schema.model_copy(
            update={
                "category_name": category.category_name,
                "category_color": category.color,
            }
        )
    return schema


@router.get("/categories", response_model=list[ElementCategory])
async def get_element_categories(session: AsyncSession = Depends(get_session)) -> list[ElementCategory]:
    """Get all element categories ordered for the UI."""
    categories = await list_element_categories(session)
    return [ElementCategory.model_validate(category) for category in categories]


@router.get(
    "/scenes/{scene_id}/elements",
    response_model=list[SceneElement],
)
async def get_scene_elements(
    scene_id: str = Path(..., description="Scene UUID"),
    session: AsyncSession = Depends(get_session),
) -> list[SceneElement]:
    """Get all elements for a specific scene."""
    scene_uuid = _parse_uuid(scene_id, "scene_id")
    elements = await list_scene_elements(session, scene_uuid)
    return [_element_to_schema(el) for el in elements]


@router.post(
    "/scenes/{scene_id}/elements",
    response_model=SceneElement,
    status_code=status.HTTP_201_CREATED,
)
async def create_scene_element_endpoint(
    scene_id: str,
    element: SceneElementCreate,
    session: AsyncSession = Depends(get_session),
) -> SceneElement:
    """Create a new scene element."""
    _parse_uuid(scene_id, "scene_id")
    if element.scene_id and element.scene_id != scene_id:
        raise HTTPException(status_code=400, detail="scene_id mismatch between path and payload.")
    payload = element.model_copy(update={"scene_id": scene_id})
    db_element = await create_scene_element(session, payload)
    return _element_to_schema(db_element)


@router.patch(
    "/scenes/{scene_id}/elements/{element_id}",
    response_model=SceneElement,
)
async def update_scene_element_endpoint(
    scene_id: str,
    element_id: int,
    payload: SceneElementUpdate,
    session: AsyncSession = Depends(get_session),
) -> SceneElement:
    """Update an existing scene element."""
    scene_uuid = _parse_uuid(scene_id, "scene_id")
    element = await update_scene_element(session, scene_uuid, element_id, payload)
    if not element:
        raise HTTPException(status_code=404, detail="Scene element not found.")
    return _element_to_schema(element)


@router.delete(
    "/scenes/{scene_id}/elements/{element_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_scene_element_endpoint(
    scene_id: str,
    element_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete a scene element."""
    scene_uuid = _parse_uuid(scene_id, "scene_id")
    deleted = await delete_scene_element(session, scene_uuid, element_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scene element not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/scenes/{scene_id}/tags",
    response_model=list[SceneTag],
)
async def get_scene_tags(
    scene_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[SceneTag]:
    """List tags assigned to a scene."""
    scene_uuid = _parse_uuid(scene_id, "scene_id")
    tags = await list_scene_tags(session, scene_uuid)
    return [SceneTag.model_validate(tag) for tag in tags]


@router.post(
    "/scenes/{scene_id}/tags",
    response_model=SceneTag,
    status_code=status.HTTP_201_CREATED,
)
async def create_scene_tag_endpoint(
    scene_id: str,
    payload: SceneTagCreate,
    session: AsyncSession = Depends(get_session),
) -> SceneTag:
    """Create a tag for a scene."""
    scene_uuid = _parse_uuid(scene_id, "scene_id")
    tag = await create_scene_tag(session, scene_uuid, payload.tag)
    return SceneTag.model_validate(tag)


@router.delete(
    "/scenes/{scene_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_scene_tag_endpoint(
    scene_id: str,
    tag_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete a scene tag."""
    scene_uuid = _parse_uuid(scene_id, "scene_id")
    deleted = await delete_scene_tag(session, scene_uuid, tag_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scene tag not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/scenes/{scene_id}/notes",
    response_model=list[SceneNote],
)
async def get_scene_notes(
    scene_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[SceneNote]:
    """List production notes for a scene."""
    scene_uuid = _parse_uuid(scene_id, "scene_id")
    notes = await list_scene_notes(session, scene_uuid)
    return [SceneNote.model_validate(note) for note in notes]


@router.post(
    "/scenes/{scene_id}/notes",
    response_model=SceneNote,
    status_code=status.HTTP_201_CREATED,
)
async def create_scene_note_endpoint(
    scene_id: str,
    payload: SceneNoteCreate,
    session: AsyncSession = Depends(get_session),
) -> SceneNote:
    """Create a production note for a scene."""
    scene_uuid = _parse_uuid(scene_id, "scene_id")
    note = await create_scene_note(session, scene_uuid, payload.note_text, payload.note_type)
    return SceneNote.model_validate(note)


@router.patch(
    "/scenes/{scene_id}/notes/{note_id}",
    response_model=SceneNote,
)
async def update_scene_note_endpoint(
    scene_id: str,
    note_id: int,
    payload: SceneNoteUpdate,
    session: AsyncSession = Depends(get_session),
) -> SceneNote:
    """Update a production note for a scene."""
    scene_uuid = _parse_uuid(scene_id, "scene_id")
    note = await update_scene_note(session, scene_uuid, note_id, payload)
    if not note:
        raise HTTPException(status_code=404, detail="Scene note not found.")
    return SceneNote.model_validate(note)


@router.delete(
    "/scenes/{scene_id}/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_scene_note_endpoint(
    scene_id: str,
    note_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete a production note from a scene."""
    scene_uuid = _parse_uuid(scene_id, "scene_id")
    deleted = await delete_scene_note(session, scene_uuid, note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scene note not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/uploads/{upload_id}/master-elements",
    response_model=list[MasterElement],
)
async def get_master_elements(
    upload_id: str,
    category_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> list[MasterElement]:
    """List unique production elements for an upload (master list)."""
    upload_uuid = _parse_uuid(upload_id, "upload_id")
    elements = await list_master_elements(session, upload_uuid, category_id)
    return [_master_element_to_schema(el) for el in elements]
