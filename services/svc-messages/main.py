"""
svc-messages – Messages microservice.
Exposes channel messages, direct messages, read status and conversations.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
import app.models  # noqa: F401

from app.modules.messages.router import router as messages_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} – Messages Service",
    description="Handles channel messages, direct messages and conversations",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(messages_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "svc-messages"}
