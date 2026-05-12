"""
svc-auth – Auth microservice.
DATABASE DISTRIBUIDA: Usa su propia BD (databases/auth.db)
"""
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./databases/auth.db"

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
from app.models.user import User  # Solo importa SU modelo

from app.modules.auth.router import router as auth_router
from app.mom.publisher import EventPublisher

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # Solo crea las tablas de SU dominio
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(
            sync_conn, tables=[User.__table__]
        ))
    logger.info(f"svc-auth: BD distribuida → {settings.DATABASE_URL}")

    connected = await EventPublisher.connect()
    if connected:
        logger.info("svc-auth: MOM Publisher conectado")
    yield
    await EventPublisher.close()
    await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} – Auth Service",
    description="Handles registration, login, JWT (BD propia: auth.db)",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "svc-auth", "database": "auth.db"}
