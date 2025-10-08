from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import RateCardModel


async def get_default_rate_cards(session: AsyncSession) -> list[RateCardModel]:
    result = await session.execute(
        select(RateCardModel).where(RateCardModel.is_default.is_(True)).order_by(RateCardModel.category)
    )
    return list(result.scalars().all())

