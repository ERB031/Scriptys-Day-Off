"""Day Out of Days (DOOD) report endpoints."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...db.session import get_session
from ...schemas.dood import DayOutOfDays, CastMemberDays
from ...repositories.dood import get_dood_report

router = APIRouter()

@router.get("/uploads/{upload_id}/dood", response_model=DayOutOfDays)
async def get_dood(
    upload_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get Day Out of Days report for a specific script upload."""
    report = await get_dood_report(session, upload_id)
    return report
