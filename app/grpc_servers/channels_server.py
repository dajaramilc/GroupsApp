"""
gRPC server implementation expuesto por svc-channels.

Permite a otros microservicios (ej. svc-messages) verificar el acceso
de un usuario a un canal sin tener que duplicar la lógica de membresía.
"""
import logging
from uuid import UUID

import grpc
from grpc import aio

from app.core.database import AsyncSessionLocal
from app.grpc_proto import channels_pb2, channels_pb2_grpc
from app.modules.channels.repository import ChannelRepository
from app.modules.groups.repository import GroupRepository

logger = logging.getLogger(__name__)


class ChannelServiceServicer(channels_pb2_grpc.ChannelServiceServicer):
    """Implementa la lógica del servicio gRPC ChannelService."""

    async def CheckChannelAccess(
        self,
        request: channels_pb2.CheckChannelAccessRequest,
        context: grpc.aio.ServicerContext,
    ) -> channels_pb2.CheckChannelAccessResponse:
        try:
            channel_uuid = UUID(request.channel_id)
            user_uuid = UUID(request.user_id)
        except ValueError:
            return channels_pb2.CheckChannelAccessResponse(
                allowed=False,
                channel_id=request.channel_id,
                group_id="",
                reason="invalid_uuid",
            )

        async with AsyncSessionLocal() as db:
            channel = await ChannelRepository.get_by_id(db, channel_uuid)
            if not channel:
                return channels_pb2.CheckChannelAccessResponse(
                    allowed=False,
                    channel_id=request.channel_id,
                    group_id="",
                    reason="channel_not_found",
                )

            member = await GroupRepository.get_member(db, channel.group_id, user_uuid)
            if not member:
                return channels_pb2.CheckChannelAccessResponse(
                    allowed=False,
                    channel_id=request.channel_id,
                    group_id=str(channel.group_id),
                    reason="not_member",
                )

            return channels_pb2.CheckChannelAccessResponse(
                allowed=True,
                channel_id=request.channel_id,
                group_id=str(channel.group_id),
                reason="ok",
            )


async def serve_grpc(port: int = 50051) -> aio.Server:
    """Inicia el servidor gRPC asíncrono. Llamado desde el lifespan de FastAPI."""
    server = aio.server()
    channels_pb2_grpc.add_ChannelServiceServicer_to_server(
        ChannelServiceServicer(), server
    )
    listen_addr = f"[::]:{port}"
    server.add_insecure_port(listen_addr)
    await server.start()
    logger.info(f"gRPC ChannelService escuchando en {listen_addr}")
    return server
