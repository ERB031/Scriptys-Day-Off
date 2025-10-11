from pydantic import BaseModel

class ActorCompensation(BaseModel):
    id: int
    actor_name: str
    daily_rate: float
    overtime_rate: float
    union_status: str
    notes: str | None = None
    assigned_characters: list[str] = []

class LocationCompensation(BaseModel):
    id: int
    location_name: str
    fee: float
    notes: str | None = None
