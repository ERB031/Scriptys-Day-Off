from pydantic import BaseModel, Field


class RateCard(BaseModel):
    id: int
    category: str
    item_name: str
    unit: str
    base_rate: float
    overtime_rate: float = Field(default=0)
    is_default: bool = False

