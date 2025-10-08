from fastapi import APIRouter

from .v1 import ingest, schedule, scenes, rate_cards

api_router = APIRouter()

api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(scenes.router, prefix="/scenes", tags=["scenes"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
api_router.include_router(rate_cards.router, prefix="/rate_cards", tags=["rate_cards"])
