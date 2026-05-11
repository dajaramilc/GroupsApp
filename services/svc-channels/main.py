"""
svc-channels – Channels microservice.
Exposes /groups/{id}/channels and /channels/* endpoints.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
import app.models  # noqa: F401

from app.modules.channels.router import router as channels_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} – Channels Service",
    description="Manages channels within groups",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(channels_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "svc-channels"}
