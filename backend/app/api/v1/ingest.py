from __future__ import annotations

import mimetypes
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_session
from ...repositories.scenes import create_script_upload, get_latest_upload
from ...schemas.scene import PageLengthRequest, PageLengthResponse, SceneUploadResponse, UploadSnapshot
from ...services.fdx_parser import FDXParser, ParsedScene
from .utils import scene_model_to_schema

router = APIRouter()


SUPPORTED_TYPES = {
    "application/vnd.finaldraft.fdx",
    "application/xml",
    "text/xml",
    "application/octet-stream",  # some browsers default for FDX
}


@router.post("/script", response_model=SceneUploadResponse)
async def ingest_script(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> SceneUploadResponse:
    file_bytes = await file.read()
    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0]

    if not content_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to detect file type.")

    if content_type not in SUPPORTED_TYPES and not (file.filename or "").lower().endswith(".fdx"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only Final Draft .fdx files are currently supported.",
        )

    parser = FDXParser()
    try:
        parsed_scenes = parser.parse(file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not parsed_scenes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No scenes were detected in the uploaded script.",
        )

    self_assign_costs(parsed_scenes)

    upload_id = str(uuid4())
    scene_models = await create_script_upload(
        session=session,
        upload_id=upload_id,
        filename=file.filename or "unknown.fdx",
        mime_type=content_type,
        parsed_scenes=parsed_scenes,
    )

    scenes = [scene_model_to_schema(model) for model in scene_models]

    return SceneUploadResponse(upload_id=upload_id, scenes=scenes)


def self_assign_costs(parsed_scenes: List[ParsedScene]) -> None:
    """
    Provide a deterministic fallback cost estimate when AI estimates are unavailable.
    The heuristic scales crew/logistics cost by page count and adds per-actor load.
    """
    base_crew_cost = 1200 + 850 + 550  # DP + AD + Gaffer
    equipment_cost = 750 + 480  # Camera + Lighting
    logistics_cost = 350 + 275  # Company move + Permit
    pages_per_day = 5.0

    for scene in parsed_scenes:
        page_factor = max(scene.page_decimal / pages_per_day, 0.4)
        cast_cost = max(len(scene.cast), 1) * 650  # treat as supporting actors for baseline
        estimated = (base_crew_cost + equipment_cost + logistics_cost) * page_factor + cast_cost
        scene.estimated_cost = round(estimated, 2)


@router.post("/calculate/eighths", response_model=PageLengthResponse)
async def calculate_eighths(payload: PageLengthRequest) -> PageLengthResponse:
    if not payload.paragraphs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No paragraph content provided.")

    parser = FDXParser()
    paragraph_types = payload.paragraph_types or ["Action"] * len(payload.paragraphs)
    if len(paragraph_types) != len(payload.paragraphs):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="paragraph_types must match the length of paragraphs.",
        )

    structured = [
        {"type": paragraph_types[idx], "text": parser.clean_text(text)}
        for idx, text in enumerate(payload.paragraphs)
    ]
    page_eighths = parser.estimate_eighths(structured)
    return PageLengthResponse(page_eighths=page_eighths, page_decimal=round(page_eighths / 8.0, 3))


@router.get("/latest", response_model=UploadSnapshot | None)
async def latest_upload(session: AsyncSession = Depends(get_session)) -> UploadSnapshot | None:
    upload = await get_latest_upload(session)
    if not upload:
        return None
    return UploadSnapshot(
        upload_id=upload.id,
        original_filename=upload.original_filename,
        total_scenes=upload.total_scenes,
        total_pages_decimal=upload.total_pages_decimal,
    )
