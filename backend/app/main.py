from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import api_router
from .core.config import settings


def get_application() -> FastAPI:
    app = FastAPI(
        title="Scripty's Day Off API",
        version="0.1.0",
        description="Backend services for screenplay breakdown, budgeting, and scheduling."
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    return app


app = get_application()

