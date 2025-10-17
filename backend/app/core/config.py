import json
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    backend_url: str = Field(default="http://localhost:8000", alias="BACKEND_URL")
    database_url: str = Field(default="postgresql+asyncpg://scripty:password@localhost:5432/scriptys_day_off", alias="DATABASE_URL")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "https://scriptys-day-aohmarkkm-erb031s-projects.vercel.app"], alias="CORS_ORIGINS")
    chat_model: str = Field(default="gemini-1.5-flash", alias="CHAT_MODEL")

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v

    class Config:
        populate_by_name = True
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

