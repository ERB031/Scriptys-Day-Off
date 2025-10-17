"""Breakdown sheet endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session
from ...repositories.scenes import get_scene_by_id, list_scenes_for_upload
from ...schemas.breakdown import BreakdownSheet
from ...services.breakdown_builder import build_breakdown_sheet, build_breakdown_sheets

router = APIRouter()


def _parse_uuid(value: str, name: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{name} must be a valid UUID.",
        ) from exc


@router.get(
    "/scenes/{scene_id}/breakdown",
    response_model=BreakdownSheet,
)
async def get_scene_breakdown(
    scene_id: str,
    session: AsyncSession = Depends(get_session),
) -> BreakdownSheet:
    """Get production breakdown for a specific scene."""
    scene_uuid = _parse_uuid(scene_id, "scene_id")
    scene = await get_scene_by_id(session, scene_uuid)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")
    return build_breakdown_sheet(scene)


@router.get(
    "/uploads/{upload_id}/breakdown-sheets",
    response_model=list[BreakdownSheet],
)
async def get_upload_breakdown_sheets(
    upload_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[BreakdownSheet]:
    """Get breakdown sheets for every scene in an upload."""
    upload_uuid = _parse_uuid(upload_id, "upload_id")
    scenes = await list_scenes_for_upload(session, upload_uuid)
    if not scenes:
        return []
    return build_breakdown_sheets(scenes)
