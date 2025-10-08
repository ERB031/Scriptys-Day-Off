import os
from functools import lru_cache
from typing import List

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_env: str = Field(default="development", alias="APP_ENV")
    backend_url: str = Field(default="http://localhost:8000", alias="BACKEND_URL")
    database_url: str = Field(default="postgresql+asyncpg://scripty:password@localhost:5432/scriptys_day_off", alias="DATABASE_URL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"], alias="CORS_ORIGINS")
    chat_model: str = Field(default="gpt-4.1-mini", alias="CHAT_MODEL")

    class Config:
        populate_by_name = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

