"""Regenerate AI content endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session

router = APIRouter()


@router.post("/synopsis/{scene_id}")
async def regenerate_synopsis(scene_id: str, session: AsyncSession = Depends(get_session)):
    """Regenerate AI synopsis for a specific scene."""
    # Placeholder for regenerating synopsis
    return {
        "scene_id": scene_id,
        "synopsis": None,
        "message": "Synopsis regeneration not yet implemented"
    }


@router.post("/elements/{scene_id}")
async def regenerate_elements(scene_id: str, session: AsyncSession = Depends(get_session)):
    """Regenerate AI-detected elements for a specific scene."""
    # Placeholder for regenerating elements
    return {
        "scene_id": scene_id,
        "elements": [],
        "message": "Element regeneration not yet implemented"
    }
