from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from ..db.models import ActorCompensationModel, LocationCompensationModel
from ..schemas.compensation import ActorCompensation, LocationCompensation

class ActorCompensationCreate(BaseModel):
    actor_name: str
    daily_rate: float
    overtime_rate: float
    union_status: str
    notes: str | None = None

class LocationCompensationCreate(BaseModel):
    location_name: str
    fee: float
    notes: str | None = None

async def get_all_actor_compensation(session: AsyncSession) -> List[ActorCompensation]:
    result = await session.execute(select(ActorCompensationModel).order_by(ActorCompensationModel.actor_name))
    actors = result.scalars().all()
    return [ActorCompensation.model_validate(actor) for actor in actors]

async def get_all_location_compensation(session: AsyncSession) -> List[LocationCompensation]:
    result = await session.execute(select(LocationCompensationModel).order_by(LocationCompensationModel.location_name))
    locations = result.scalars().all()
    return [
        LocationCompensation.model_validate(location, update={"fee": location.daily_fee})
        for location in locations
    ]

async def update_actor_compensation(session: AsyncSession, actor_id: int, data: ActorCompensation) -> ActorCompensation:
    actor = await session.get(ActorCompensationModel, actor_id)
    if not actor:
        raise Exception("Actor not found")

    actor.actor_name = data.actor_name
    actor.daily_rate = data.daily_rate
    actor.overtime_rate = data.overtime_rate
    actor.union_status = data.union_status
    actor.notes = data.notes

    await session.commit()
    await session.refresh(actor)

    return ActorCompensation.model_validate(actor)

async def create_actor_compensation(session: AsyncSession, data: ActorCompensationCreate) -> ActorCompensationModel:
    actor = ActorCompensationModel(**data.model_dump())
    session.add(actor)
    await session.commit()
    await session.refresh(actor)
    return actor

async def update_location_compensation(session: AsyncSession, location_id: int, data: LocationCompensation) -> LocationCompensation:
    location = await session.get(LocationCompensationModel, location_id)
    if not location:
        raise Exception("Location not found")

    location.location_name = data.location_name
    location.daily_fee = data.fee
    location.notes = data.notes

    await session.commit()
    await session.refresh(location)

    return LocationCompensation.model_validate(location, update={"fee": location.daily_fee})

async def create_location_compensation(session: AsyncSession, data: LocationCompensationCreate) -> LocationCompensationModel:
    location = LocationCompensationModel(**data.model_dump())
    session.add(location)
    await session.commit()
    await session.refresh(location)
    return location