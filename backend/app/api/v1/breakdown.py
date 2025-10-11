"""Breakdown sheet endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session

router = APIRouter()


@router.get("/{scene_id}")
async def get_scene_breakdown(scene_id: str, session: AsyncSession = Depends(get_session)):
    """Get production breakdown for a specific scene."""
    return {
        "scene_id": scene_id,
        "elements": [],
        "notes": [],
        "tags": []
    }
