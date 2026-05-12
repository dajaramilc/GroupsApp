"""
Centralised application settings loaded from environment variables / .env file.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "GroupsApp"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://groupsapp:groupsapp@db:5432/groupsapp"

    # ── JWT ──────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── File storage ─────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # ── Presence ─────────────────────────────────────────
    PRESENCE_TIMEOUT_SECONDS: int = 120  # offline after 2 min without heartbeat

    # ── MOM (RabbitMQ) ────────────────────────────────────
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
