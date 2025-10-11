from fastapi import APIRouter

from .v1 import ingest, schedule, scenes, rate_cards, compensation, elements, breakdown, regenerate, dood

api_router = APIRouter()

api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
api_router.include_router(scenes.router, prefix="/scenes", tags=["scenes"])
api_router.include_router(rate_cards.router, prefix="/rate-cards", tags=["rate-cards"])
api_router.include_router(compensation.router, prefix="/compensation", tags=["compensation"])
api_router.include_router(elements.router, prefix="/elements", tags=["elements"])
api_router.include_router(breakdown.router, prefix="/breakdown", tags=["breakdown"])
api_router.include_router(regenerate.router, prefix="/regenerate", tags=["regenerate"])
api_router.include_router(dood.router, prefix="/dood", tags=["dood"])
