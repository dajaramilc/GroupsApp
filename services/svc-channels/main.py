"""
svc-channels – Channels microservice.
Expone:
- REST (puerto 8004) — endpoints /groups/{id}/channels y /channels/*
- gRPC (puerto 50051) — ChannelService.CheckChannelAccess para uso interno
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import engine, Base
import app.models  # noqa: F401 – register all ORM models

from app.modules.channels.router import router as channels_router
from app.grpc_servers.channels_server import serve_grpc

# Asegurar nivel de log INFO para ver los mensajes de arranque del gRPC server
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas (dev convenience)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Arrancar gRPC server en paralelo a FastAPI
    grpc_server = await serve_grpc(port=50051)
    logger.info("svc-channels listo: REST:8004 + gRPC:50051")

    yield

    # Apagado ordenado
    await grpc_server.stop(grace=5)
    await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} – Channels Service",
    description="Manages channels within groups (REST + gRPC interno)",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(channels_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "svc-channels"}
