"""Compensation management endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session
from ...schemas.compensation import ActorCompensation, LocationCompensation
from ...repositories.compensation import (
    get_all_actor_compensation,
    get_all_location_compensation,
    update_actor_compensation as update_actor_compensation_repo,
    update_location_compensation as update_location_compensation_repo,
    create_actor_compensation as create_actor_compensation_repo,
    ActorCompensationCreate,
    create_location_compensation as create_location_compensation_repo,
    LocationCompensationCreate,
)

router = APIRouter()


@router.get("/actors", response_model=List[ActorCompensation])
async def get_actor_compensation(session: AsyncSession = Depends(get_session)):
    """Get all actor compensation records."""
    return await get_all_actor_compensation(session)


@router.post("/actors", response_model=ActorCompensation)
async def create_actor_compensation(
    data: ActorCompensationCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new actor compensation record."""
    try:
        actor = await create_actor_compensation_repo(session, data)
        return ActorCompensation.model_validate(actor)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations", response_model=List[LocationCompensation])
async def get_location_compensation(session: AsyncSession = Depends(get_session)):
    """Get all location compensation records."""
    return await get_all_location_compensation(session)


@router.post("/locations", response_model=LocationCompensation)
async def create_location_compensation(
    data: LocationCompensationCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new location compensation record."""
    try:
        location = await create_location_compensation_repo(session, data)
        return LocationCompensation.model_validate(location, update={"fee": location.daily_fee})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/actors/{actor_id}", response_model=ActorCompensation)
async def update_actor_compensation(
    actor_id: int,
    data: ActorCompensation,
    session: AsyncSession = Depends(get_session),
):
    """Update an actor's compensation record."""
    try:
        return await update_actor_compensation_repo(session, actor_id, data)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/locations/{location_id}", response_model=LocationCompensation)
async def update_location_compensation(
    location_id: int,
    data: LocationCompensation,
    session: AsyncSession = Depends(get_session),
):
    """Update a location's compensation record."""
    try:
        return await update_location_compensation_repo(session, location_id, data)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))