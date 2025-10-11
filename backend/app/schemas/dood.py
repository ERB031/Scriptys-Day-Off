from pydantic import BaseModel
from typing import List, Dict

class CastMemberDays(BaseModel):
    cast_member_name: str
    days: Dict[int, str] # day_number -> status (e.g., 'W', 'H', 'T', 'F')

class DayOutOfDays(BaseModel):
    shooting_days: List[int]
    cast_members: List[CastMemberDays]
