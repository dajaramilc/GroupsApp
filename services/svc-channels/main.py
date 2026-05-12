"""
svc-channels – Channels microservice.
DATABASE DISTRIBUIDA: Usa su propia BD (databases/channels.db)
Expone:
- REST (puerto 8004) — endpoints /groups/{id}/channels y /channels/*
- gRPC (puerto 50051) — ChannelService.CheckChannelAccess para uso interno
"""
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./databases/channels.db"

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import engine, Base
from app.models.channel import Channel
from app.models.group import Group, GroupMember  # Necesarios para gRPC CheckChannelAccess

from app.modules.channels.router import router as channels_router
from app.grpc_servers.channels_server import serve_grpc
from app.mom.consumer import EventConsumer
from app.core.database import AsyncSessionLocal
from app.modules.channels.repository import ChannelRepository
from app.modules.groups.repository import GroupRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Consumer MOM para replicación de datos de grupos
group_consumer = EventConsumer(
    queue_name="svc-channels.groups",
    routing_keys=["group.created", "group.member.added"],
)

async def handle_group_event(event_data: dict):
    """Replicar datos de grupos a channels.db"""
    event_type = event_data.get("event_type", "")
    
    try:
        async with AsyncSessionLocal() as db:
            if event_type == "group.created":
                from uuid import UUID
                group_id = UUID(event_data["group_id"])
                creator_id = UUID(event_data["creator_id"])
                # Replicar grupo
                await GroupRepository.create(db, event_data.get("name", "Unknown"), event_data.get("description", ""), creator_id, id=group_id)
                # Crear canal general
                await ChannelRepository.create(db, group_id, "general", "Canal general del grupo", creator_id)
                await db.commit()
                logger.info(f"Replicado grupo {group_id} y creado canal #general")
                
            elif event_type == "group.member.added":
                from uuid import UUID
                group_id = UUID(event_data["group_id"])
                user_id = UUID(event_data["user_id"])
                # Replicar miembro
                from app.models.group import GroupRole
                role = GroupRole.ADMIN if event_data.get("role") == "admin" else GroupRole.MEMBER
                await GroupRepository.add_member(db, group_id, user_id, role)
                await db.commit()
                logger.info(f"Replicado miembro {user_id} al grupo {group_id}")
    except Exception as e:
        logger.error(f"Error procesando evento {event_type}: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(
            sync_conn, tables=[Channel.__table__, Group.__table__, GroupMember.__table__]
        ))

    grpc_server = await serve_grpc(port=50051)
    await group_consumer.start(handle_group_event)
    logger.info("svc-channels listo: REST:8004 + gRPC:50051 + MOM Consumer (BD: channels.db)")

    yield

    await group_consumer.stop()
    await grpc_server.stop(grace=5)
    await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} – Channels Service",
    description="Manages channels within groups (REST + gRPC, BD propia: channels.db)",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(channels_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "svc-channels", "database": "channels.db"}
