from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session
from ...repositories.rate_cards import get_default_rate_cards
from ...schemas.rate_card import RateCard

router = APIRouter()


@router.get("", response_model=list[RateCard])
async def list_rate_cards(session: AsyncSession = Depends(get_session)) -> list[RateCard]:
    rows = await get_default_rate_cards(session)
    return [
        RateCard(
            id=row.id,
            category=row.category,
            item_name=row.item_name,
            unit=row.unit,
            base_rate=float(row.base_rate),
            overtime_rate=float(row.overtime_rate),
            is_default=row.is_default,
        )
        for row in rows
    ]

