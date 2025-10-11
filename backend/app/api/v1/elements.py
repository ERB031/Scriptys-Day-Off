"""Scene elements endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session
from ...schemas.elements import SceneElement, SceneElementCreate
from ...repositories.elements import create_scene_element as create_scene_element_repo

router = APIRouter()


@router.get("/categories")
async def get_element_categories(session: AsyncSession = Depends(get_session)):
    """Get all element categories."""
    return []


@router.get("/{scene_id}")
async def get_scene_elements(scene_id: str, session: AsyncSession = Depends(get_session)):
    """Get all elements for a specific scene."""
    return []


@router.post("/", response_model=SceneElement)
async def create_scene_element(
    element: SceneElementCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new scene element."""
    try:
        db_element = await create_scene_element_repo(session, element)
        return SceneElement.model_validate(db_element)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))