from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session
from ...repositories.scenes import get_latest_upload, list_scenes_for_upload
from ...schemas.scene import Scene
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

    return [scene_model_to_schema(scene) for scene in scenes]
