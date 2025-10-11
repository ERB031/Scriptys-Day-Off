from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session
from ...repositories.scenes import (
    get_latest_upload,
    list_scenes_for_upload,
    update_scene_metadata,
    update_scenes_batch,
    delete_scene as delete_scene_record,
    get_character_assignment_lookup,
)
from ...schemas.scene import Scene, SceneUpdateRequest, BatchSceneAssignmentRequest
from .utils import scene_model_to_schema

router = APIRouter()


@router.get("", response_model=list[Scene])
async def list_scenes(
    upload_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> list[Scene]:
    target_upload_id = upload_id
    if not target_upload_id:
        latest_upload = await get_latest_upload(session)
        if not latest_upload:
            return []
        target_upload_id = latest_upload.id

    scenes = await list_scenes_for_upload(session, target_upload_id)
    if not scenes:
        if upload_id:
            raise HTTPException(status_code=404, detail="No scenes found for upload.")
        return []

    assignment_lookup = await get_character_assignment_lookup(session, target_upload_id)
    return [scene_model_to_schema(scene, assignment_lookup) for scene in scenes]


@router.patch("/{scene_id}", response_model=Scene)
async def update_scene(
    scene_id: str,
    payload: SceneUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> Scene:
    update_fields = payload.model_dump(exclude_unset=True)
    updated_scene = await update_scene_metadata(session, scene_id, update_fields)
    if not updated_scene:
        raise HTTPException(status_code=404, detail="Scene not found.")

    assignment_lookup = await get_character_assignment_lookup(session, updated_scene.upload_id)
    return scene_model_to_schema(updated_scene, assignment_lookup)


@router.post("/assignments/batch", response_model=list[Scene])
async def assign_scenes_batch(
    payload: BatchSceneAssignmentRequest,
    session: AsyncSession = Depends(get_session),
) -> list[Scene]:
    update_fields: dict[str, object] = {}
    if payload.location is not None:
        update_fields["location"] = payload.location
    if payload.script_day is not None:
        update_fields["script_day"] = payload.script_day

    if not update_fields:
        raise HTTPException(status_code=400, detail="At least one of location or script_day must be provided.")

    scenes = await update_scenes_batch(session, payload.scene_ids, update_fields)
    if not scenes:
        raise HTTPException(status_code=404, detail="No matching scenes found for assignment.")

    assignment_lookup = await get_character_assignment_lookup(session, scenes[0].upload_id)
    return [scene_model_to_schema(scene, assignment_lookup) for scene in scenes]


@router.delete("/{scene_id}", status_code=204)
async def delete_scene(scene_id: str, session: AsyncSession = Depends(get_session)) -> None:
    deleted = await delete_scene_record(session, scene_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scene not found.")
