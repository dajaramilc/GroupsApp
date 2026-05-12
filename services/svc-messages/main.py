"""
svc-messages – Messages microservice.
DATABASE DISTRIBUIDA: Usa su propia BD (databases/messages.db)
Actúa como PRODUCTOR MOM: publica eventos 'message.sent' en RabbitMQ.
"""
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./databases/messages.db"

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
from app.models.message import Message
from app.models.direct_conversation import DirectConversation
from app.models.message_status import MessageStatus

from app.modules.messages.router import router as messages_router
from app.mom.publisher import EventPublisher

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(
            sync_conn,
            tables=[Message.__table__, DirectConversation.__table__, MessageStatus.__table__]
        ))

    connected = await EventPublisher.connect()
    if connected:
        logger.info("svc-messages: MOM Publisher conectado a RabbitMQ")
    else:
        logger.warning("svc-messages: MOM Publisher NO disponible")

    logger.info(f"svc-messages listo (BD: messages.db)")

    yield

    await EventPublisher.close()
    await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} – Messages Service",
    description="Handles channel/direct messages (MOM producer, BD propia: messages.db)",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(messages_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "svc-messages", "database": "messages.db", "mom_publisher": "active"}
