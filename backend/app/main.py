from contextlib import asynccontextmanager

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import api_router
from .core.config import settings
from .db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database connection pool is ready
    async with engine.begin() as conn:
        # Test the connection
        await conn.run_sync(lambda _: None)
    yield
    # Shutdown: close all database connections
    await engine.dispose()


def get_application() -> FastAPI:
    app = FastAPI(
        title="Scripty's Day Off API",
        version="0.1.0",
        description="Backend services for screenplay breakdown, budgeting, and scheduling.",
        lifespan=lifespan
    )

    # Ensure settings are loaded
    loaded_settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=loaded_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    return app


app = get_application()
