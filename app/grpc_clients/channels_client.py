"""
Cliente gRPC para consumir ChannelService desde svc-messages.

Mantiene un canal persistente al servicio svc-channels.
La dirección se resuelve desde la variable de entorno SVC_CHANNELS_GRPC_ADDR
(formato host:puerto). Default: svc-channels:50051 (DNS de Kubernetes).
"""
import os
import logging
from uuid import UUID

import grpc
from grpc import aio

from app.grpc_proto import channels_pb2, channels_pb2_grpc

logger = logging.getLogger(__name__)

GRPC_ADDR = os.getenv("SVC_CHANNELS_GRPC_ADDR", "localhost:50051")
GRPC_TIMEOUT_SECONDS = float(os.getenv("SVC_CHANNELS_GRPC_TIMEOUT", "3.0"))


class ChannelsGrpcClient:
    """Singleton para el canal gRPC al servicio svc-channels."""

    _channel: aio.Channel | None = None
    _stub: channels_pb2_grpc.ChannelServiceStub | None = None

    @classmethod
    def get_stub(cls) -> channels_pb2_grpc.ChannelServiceStub:
        if cls._channel is None:
            cls._channel = aio.insecure_channel(GRPC_ADDR)
            cls._stub = channels_pb2_grpc.ChannelServiceStub(cls._channel)
            logger.info(f"Cliente gRPC svc-channels inicializado contra {GRPC_ADDR}")
        return cls._stub

    @classmethod
    async def close(cls):
        if cls._channel is not None:
            await cls._channel.close()
            cls._channel = None
            cls._stub = None


async def check_channel_access(channel_id: UUID, user_id: UUID) -> tuple[bool, str, str]:
    """
    Devuelve (allowed, group_id, reason). En caso de error de transporte gRPC,
    retorna (False, "", "grpc_unavailable").
    """
    stub = ChannelsGrpcClient.get_stub()
    request = channels_pb2.CheckChannelAccessRequest(
        channel_id=str(channel_id),
        user_id=str(user_id),
    )
    try:
        response = await stub.CheckChannelAccess(request, timeout=GRPC_TIMEOUT_SECONDS)
        return response.allowed, response.group_id, response.reason
    except grpc.aio.AioRpcError as error_rpc:
        logger.warning(
            f"gRPC CheckChannelAccess falló (code={error_rpc.code()}): {error_rpc.details()}"
        )
        return False, "", "grpc_unavailable"
