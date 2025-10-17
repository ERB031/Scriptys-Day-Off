from contextlib import asynccontextmanager

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import api_router
from .core.config import settings
from .db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: attempt to connect to database
    import logging
    logger = logging.getLogger(__name__)

    try:
        async with engine.begin() as conn:
            # Test the connection
            await conn.run_sync(lambda _: None)
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.warning(f"Could not connect to database: {e}")
        logger.warning("Application will start without database connectivity")

    yield

    # Shutdown: close all database connections
    try:
        await engine.dispose()
    except Exception as e:
        logger.warning(f"Error during database cleanup: {e}")


def get_application() -> FastAPI:
    app = FastAPI(
        title="Scripty's Day Off API",
        version="0.1.0",
        description="Backend services for screenplay breakdown, budgeting, and scheduling.",
        lifespan=lifespan
    )

    # Ensure settings are loaded
    loaded_settings = settings

    # Configure CORS with support for regex patterns
    cors_origins = loaded_settings.cors_origins.copy()

    # Add regex pattern for Vercel preview deployments if in production
    if loaded_settings.app_env == "production":
        # This will match all Vercel preview URLs
        cors_origins.append("https://*.vercel.app")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_origin_regex=r"https://.*\.vercel\.app",
    )

    app.include_router(api_router, prefix="/api/v1")

    return app


app = get_application()
