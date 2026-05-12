"""
svc-groups – Groups microservice.
DATABASE DISTRIBUIDA: Usa su propia BD (databases/groups.db)
"""
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./databases/groups.db"

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
from app.models.group import Group, GroupMember

from app.modules.groups.router import router as groups_router


from app.mom.publisher import EventPublisher
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(
            sync_conn, tables=[Group.__table__, GroupMember.__table__]
        ))
    
    connected = await EventPublisher.connect()
    if connected:
        logger.info("svc-groups: MOM Publisher conectado")

    yield
    
    await EventPublisher.close()
    await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} – Groups Service",
    description="Manages groups and memberships (BD propia: groups.db)",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(groups_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "svc-groups", "database": "groups.db"}
