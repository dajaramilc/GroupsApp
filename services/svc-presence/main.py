"""
svc-presence – Presence microservice.
DATABASE DISTRIBUIDA: Usa su propia BD (databases/presence.db)
También actúa como CONSUMIDOR MOM: escucha eventos 'message.sent'
para actualizar automáticamente el estado de presencia del remitente.
"""
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./databases/presence.db"

import logging
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.models.presence import Presence

from app.modules.presence.router import router as presence_router
from app.modules.presence.repository import PresenceRepository
from app.mom.consumer import EventConsumer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Consumer MOM
presence_consumer = EventConsumer(
    queue_name="svc-presence.events",
    routing_keys=["message.sent", "user.registered"],
)


async def handle_event(event_data: dict):
    """
    Callback del consumer MOM.
    Cuando recibe un evento 'message.sent', actualiza el last_seen del remitente.
    """
    event_type = event_data.get("event_type", "")

    if event_type == "message.sent":
        sender_id = event_data.get("sender_id", "")
        msg_type = event_data.get("message_type", "")
        logger.info(
            f"MOM Handler: Usuario {sender_id[:8]}... envió mensaje ({msg_type}). "
            f"Actualizando presencia."
        )
        try:
            async with AsyncSessionLocal() as db:
                await PresenceRepository.upsert_online(db, UUID(sender_id))
                await db.commit()
        except Exception as e:
            logger.error(f"MOM Handler: Error actualizando presencia: {e}")

    elif event_type == "user.registered":
        username = event_data.get("username", "")
        logger.info(f"MOM Handler: Nuevo usuario registrado: {username}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(
            sync_conn, tables=[Presence.__table__]
        ))

    await presence_consumer.start(handle_event)
    logger.info("svc-presence listo: REST:8007 + MOM Consumer (BD: presence.db)")

    yield

    await presence_consumer.stop()
    await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} – Presence Service",
    description="Tracks user online/offline status (MOM consumer, BD propia: presence.db)",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(presence_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "svc-presence", "database": "presence.db", "mom_consumer": "active"}
