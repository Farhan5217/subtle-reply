import sys
from typing import List, Optional

from pydantic import (
    AnyHttpUrl,
    HttpUrl,
    PostgresDsn,
    StrictStr,
    validator,
)
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: StrictStr = "FastAPI Backend"
    API_PATH: StrictStr = "/api/v1"
    FRONTEND_URL: AnyHttpUrl = "http://localhost:3000"
    SENTRY_DSN: Optional[HttpUrl] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 7 * 24 * 60  # 7 days
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    TEST_DATABASE_URL: Optional[PostgresDsn]
    DATABASE_URL: PostgresDsn
    ASYNC_DATABASE_URL: Optional[PostgresDsn]

    @validator("DATABASE_URL", pre=True)
    def build_test_database_url(cls, v: Optional[PostgresDsn], values):
        """Overrides DATABASE_URL with TEST_DATABASE_URL in test environment."""
        if "pytest" in sys.modules:
            if not values.get("TEST_DATABASE_URL"):
                raise ValueError("pytest detected, but TEST_DATABASE_URL is not set in environment")
            return values["TEST_DATABASE_URL"]
        if v:
            v = v.replace("postgres://", "postgresql://")
        return v

    @validator("ASYNC_DATABASE_URL", pre=True, always=True)
    def build_async_database_url(cls, v: Optional[PostgresDsn], values):
        """Builds ASYNC_DATABASE_URL from DATABASE_URL."""
        db_url = values.get("DATABASE_URL")
        if db_url:
            async_url = db_url.unicode_string().replace("postgresql", "postgresql+asyncpg", 1)
            return PostgresDsn(async_url)
        return v

    GOOGLE_OAUTH_CLIENT_ID: StrictStr = ""
    GOOGLE_OAUTH_CLIENT_SECRET: StrictStr = ""

    OPENAI_API_KEY: StrictStr = ""

    SECRET_KEY: StrictStr

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
