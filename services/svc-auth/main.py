"""
svc-auth – Authentication microservice.
Exposes only the /auth/* endpoints.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
import app.models  # noqa: F401 – register all ORM models

from app.modules.auth.router import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} – Auth Service",
    description="Handles registration, login and JWT issuance",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "svc-auth"}
