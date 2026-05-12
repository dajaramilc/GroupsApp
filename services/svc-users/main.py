"""
svc-users – Users microservice.
DATABASE DISTRIBUIDA: Comparte BD con auth (databases/auth.db) — mismo dominio de usuarios.
"""
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./databases/auth.db"

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
from app.models.user import User

from app.modules.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(
            sync_conn, tables=[User.__table__]
        ))
    yield
    await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} – Users Service",
    description="User search and profiles (BD compartida con auth: auth.db)",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(users_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "svc-users", "database": "auth.db"}
