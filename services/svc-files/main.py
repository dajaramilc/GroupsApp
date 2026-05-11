"""
svc-files – Files microservice.
Exposes attachment upload/download endpoints.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
import app.models  # noqa: F401

from app.modules.files.router import router as files_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} – Files Service",
    description="Manages file uploads and attachment retrieval",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(files_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "svc-files"}
