"""
GroupsApp – FastAPI application entry point.

Registers all module routers and configures the application.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.database import engine, Base

# Import all models so they are registered with Base.metadata
import app.models  # noqa: F401

# Module routers
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.groups.router import router as groups_router
from app.modules.channels.router import router as channels_router
from app.modules.messages.router import router as messages_router
from app.modules.files.router import router as files_router
from app.modules.presence.router import router as presence_router

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup (dev convenience; use Alembic in production)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Messaging platform focused on groups and channels",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Register routers ────────────────────────────────────
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(groups_router)
app.include_router(channels_router)
app.include_router(messages_router)
app.include_router(files_router)
app.include_router(presence_router)

# ── Static files & frontend ─────────────────────────────
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(STATIC_DIR / "index.html")

