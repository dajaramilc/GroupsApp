"""
svc-users – Users microservice.
Exposes only the /users/* endpoints (profile, search).
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
import app.models  # noqa: F401

from app.modules.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} – Users Service",
    description="Manages user profiles and search",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(users_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "svc-users"}
