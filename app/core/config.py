"""
Configuración centralizada de la aplicación.
Carga valores desde variables de entorno o archivo .env.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "GroupsApp"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://groupsapp:groupsapp@db:5432/groupsapp"

    # ── JWT ──────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas

    # ── File storage ─────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # ── S3 Storage (producción) ──────────────────────────
    # Cambiar STORAGE_BACKEND a "s3" para usar S3 en vez de disco local
    STORAGE_BACKEND: str = "local"
    S3_BUCKET_UPLOADS: str = ""
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # ── CORS (producción) ────────────────────────────────
    # Orígenes permitidos separados por coma. Ej: "https://d123.cloudfront.net,https://midominio.com"
    CORS_ORIGINS: str = "*"

    # ── Presence ─────────────────────────────────────────
    PRESENCE_TIMEOUT_SECONDS: int = 120  # offline después de 2 min sin heartbeat

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
