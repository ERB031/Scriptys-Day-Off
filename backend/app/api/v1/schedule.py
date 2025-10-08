from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session
from ...repositories.scenes import get_latest_upload, list_scenes_for_upload
from ...schemas.schedule import AutoScheduleRequest, DayPlan
from ...services.exporters import DayPlanExporter
from ...services.scheduler import AutoScheduler
from .utils import scene_model_to_schema

router = APIRouter()


@router.get("/days", response_model=list[DayPlan])
async def list_day_plans(
    upload_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> list[DayPlan]:
    plans = await _build_day_plans(session, upload_id)
    return plans


@router.post("/auto", response_model=list[DayPlan])
async def auto_schedule(
    payload: AutoScheduleRequest,
    session: AsyncSession = Depends(get_session),
) -> list[DayPlan]:
    scenes = await list_scenes_for_upload(session, payload.upload_id)
    if not scenes:
        raise HTTPException(status_code=404, detail="No scenes found for upload.")

    scheduler = AutoScheduler()
    scene_schemas = [scene_model_to_schema(scene) for scene in scenes]
    return scheduler.build(scene_schemas)


@router.get("/export.csv")
async def export_day_budgets_csv(
    upload_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    plans = await _build_day_plans(session, upload_id)
    exporter = DayPlanExporter(plans)
    csv_payload = exporter.to_csv()
    return StreamingResponse(
        iter([csv_payload]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="day_budgets.csv"'},
    )


@router.get("/export.pdf")
async def export_day_budgets_pdf(
    upload_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    plans = await _build_day_plans(session, upload_id)
    exporter = DayPlanExporter(plans)
    pdf_bytes = exporter.to_pdf()
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="day_budgets.pdf"'},
    )


async def _build_day_plans(session: AsyncSession, upload_id: str | None) -> list[DayPlan]:
    target_upload_id = upload_id
    if not target_upload_id:
        latest_upload = await get_latest_upload(session)
        if not latest_upload:
            return []
        target_upload_id = latest_upload.id

    scenes = await list_scenes_for_upload(session, target_upload_id)
    scene_schemas = [scene_model_to_schema(scene) for scene in scenes]
    scheduler = AutoScheduler()
    return scheduler.build(scene_schemas)
