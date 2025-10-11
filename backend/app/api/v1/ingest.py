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
from ...services.scene_summarizer import SceneSummarizer
from ...services.element_detector import ElementDetector
from ...services.character_analyzer import CharacterAnalyzer
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
    import logging
    logger = logging.getLogger(__name__)

    file_bytes = await file.read()
    logger.info(f"Received file: {file.filename}, size: {len(file_bytes)} bytes")

    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0]
    logger.info(f"Content type: {content_type}")

    if not content_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to detect file type.")

    if content_type not in SUPPORTED_TYPES and not (file.filename or "").lower().endswith(".fdx"):
        logger.error(f"Unsupported content type: {content_type} for file: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only Final Draft .fdx files are currently supported.",
        )

    parser = FDXParser()
    try:
        logger.info("Starting FDX parsing...")
        parsed_scenes = parser.parse(file_bytes)
        logger.info(f"Parsing completed. Found {len(parsed_scenes)} scenes.")
    except ValueError as exc:
        logger.error(f"Parsing failed: {str(exc)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected parsing error: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Parsing error: {str(exc)}") from exc

    if not parsed_scenes:
        logger.warning("No scenes were detected in the uploaded script")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No scenes were detected in the uploaded script.",
        )

    summarizer = SceneSummarizer()
    try:
        synopsis_map = await summarizer.generate_synopses(parsed_scenes)
        for scene in parsed_scenes:
            scene.synopsis = synopsis_map.get(scene.id)
    except Exception as exc:
        logger.warning("Scene summarization failed; continuing without synopses. error=%s", exc)

    # Detect elements using Gemini
    detector = ElementDetector()
    try:
        elements_map = await detector.detect_elements(parsed_scenes)
        for scene in parsed_scenes:
            detected_elements = elements_map.get(scene.id, [])
            # Merge with existing elements, avoiding duplicates
            existing_element_keys = {
                (el.category, el.name.lower()) for el in scene.elements
            }
            for detected_element in detected_elements:
                element_key = (detected_element.category, detected_element.name.lower())
                if element_key not in existing_element_keys:
                    scene.elements.append(detected_element)
                    existing_element_keys.add(element_key)
    except Exception as exc:
        logger.warning("Element detection failed; continuing without AI-detected elements. error=%s", exc)

    # Analyze characters using Gemini
    char_analyzer = CharacterAnalyzer()
    try:
        character_analysis = await char_analyzer.analyze_characters(parsed_scenes)
        logger.info(f"Character analysis completed: {character_analysis}")
    except Exception as exc:
        logger.warning("Character analysis failed; continuing without it. error=%s", exc)

    self_assign_costs(parsed_scenes)

    upload_id = str(uuid4())
    upload_id_returned, scenes = await create_script_upload(
        session=session,
        upload_id=upload_id,
        filename=file.filename or "unknown.fdx",
        mime_type=content_type,
        parsed_scenes=parsed_scenes,
    )

    return SceneUploadResponse(upload_id=upload_id_returned, scenes=scenes)


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
        upload_id=str(upload.id),
        original_filename=upload.original_filename,
        total_scenes=upload.total_scenes,
        total_pages_decimal=upload.total_pages_decimal,
    )
