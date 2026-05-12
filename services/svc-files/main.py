"""
svc-files – Files microservice.
DATABASE DISTRIBUIDA: Usa su propia BD (databases/files.db)
"""
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./databases/files.db"

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
from app.models.attachment import MessageAttachment

from app.modules.files.router import router as files_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(
            sync_conn, tables=[MessageAttachment.__table__]
        ))
    yield
    await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} – Files Service",
    description="Manages file uploads and attachments (BD propia: files.db)",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(files_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "svc-files", "database": "files.db"}
