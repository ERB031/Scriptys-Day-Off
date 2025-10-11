from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session
from ...repositories.scenes import (
    get_latest_upload,
    list_scenes_for_upload,
    get_character_assignment_lookup,
    get_schedule_day_overrides,
    upsert_schedule_day_location,
)
from ...schemas.schedule import AutoScheduleRequest, DayPlan, DayLocationUpdateRequest
from ...services.exporters import DayPlanExporter
from ...services.scheduler import AutoScheduler
from ...services.reports import FlipboardGenerator, DayOutOfDaysGenerator
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
        return []

    assignment_lookup = await get_character_assignment_lookup(session, payload.upload_id)
    scheduler = AutoScheduler()
    scene_schemas = [scene_model_to_schema(scene, assignment_lookup) for scene in scenes]
    try:
        return scheduler.build(scene_schemas)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


@router.patch("/days/{script_day}/location", response_model=list[DayPlan])
async def update_day_location(
    script_day: int,
    payload: DayLocationUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> list[DayPlan]:
    if not 1 <= script_day <= 20:
        raise HTTPException(status_code=400, detail="script_day must be between 1 and 20.")

    target_upload_id = payload.upload_id
    if not target_upload_id:
        latest_upload = await get_latest_upload(session)
        if not latest_upload:
            raise HTTPException(status_code=404, detail="No uploads available.")
        target_upload_id = str(latest_upload.id)

    await upsert_schedule_day_location(session, target_upload_id, script_day, payload.location)
    return await _build_day_plans(session, target_upload_id)


async def _build_day_plans(session: AsyncSession, upload_id: str | None) -> list[DayPlan]:
    target_upload_id = upload_id
    if not target_upload_id:
        latest_upload = await get_latest_upload(session)
        if not latest_upload:
            return []
        target_upload_id = latest_upload.id

    scenes = await list_scenes_for_upload(session, target_upload_id)
    assignment_lookup = await get_character_assignment_lookup(session, target_upload_id)
    scene_schemas = [scene_model_to_schema(scene, assignment_lookup) for scene in scenes]
    scheduler = AutoScheduler()
    try:
        plans = scheduler.build(scene_schemas)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    overrides = await get_schedule_day_overrides(session, target_upload_id)
    if not overrides:
        return plans

    for plan in plans:
        script_days = sorted({scene.script_day for scene in plan.scenes if scene.script_day is not None})
        if len(script_days) != 1:
            continue
        override = overrides.get(script_days[0])
        if not override:
            continue
        if override.shooting_location:
            plan.shooting_location = override.shooting_location
            # Ensure override appears first in location summary.
            normalized_summary = [loc for loc in plan.location_summary if loc != override.shooting_location]
            plan.location_summary = [override.shooting_location, *normalized_summary]

    return plans


@router.get("/flipboard")
async def get_flipboard_schedule(
    upload_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Get shooting schedule in flipboard/one-liner format."""
    plans = await _build_day_plans(session, upload_id)
    if not plans:
        return JSONResponse(content={"days": []})

    generator = FlipboardGenerator(plans)
    return JSONResponse(content={"days": generator.to_dict()})


@router.get("/dood")
async def get_day_out_of_days(
    upload_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Get Day Out Of Days (DOOD) report showing actor work days."""
    plans = await _build_day_plans(session, upload_id)
    if not plans:
        return JSONResponse(content={"actors": [], "legend": {}})

    generator = DayOutOfDaysGenerator(plans)
    return JSONResponse(content=generator.to_dict())


@router.get("/dood/export.pdf")
async def export_dood_pdf(
    upload_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """Export Day Out Of Days as PDF."""
    plans = await _build_day_plans(session, upload_id)
    generator = DayOutOfDaysGenerator(plans)
    pdf_bytes = generator.to_pdf()
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="day_out_of_days.pdf"'},
    )


@router.get("/stripboard/export.pdf")
async def export_stripboard_pdf(
    upload_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """Export stripboard/shooting schedule as PDF."""
    plans = await _build_day_plans(session, upload_id)
    generator = FlipboardGenerator(plans)
    pdf_bytes = generator.to_pdf()
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="stripboard.pdf"'},
    )
