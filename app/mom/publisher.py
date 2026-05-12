"""
MOM — Publisher (Productor de eventos).

Publica eventos en RabbitMQ usando exchange tipo 'topic'.
Diseñado con resiliencia: si RabbitMQ no está disponible,
el servicio sigue funcionando (graceful degradation).
"""
import logging
from typing import Optional

import aio_pika
from aio_pika import ExchangeType

from app.core.config import settings
from app.mom.events import BaseEvent

logger = logging.getLogger(__name__)

# Nombre del exchange compartido por todos los microservicios
EXCHANGE_NAME = "groupsapp.events"


class EventPublisher:
    """Singleton para publicar eventos en RabbitMQ."""

    _connection: Optional[aio_pika.abc.AbstractRobustConnection] = None
    _channel: Optional[aio_pika.abc.AbstractChannel] = None
    _exchange: Optional[aio_pika.abc.AbstractExchange] = None

    @classmethod
    async def connect(cls) -> bool:
        """Establece conexión con RabbitMQ. Retorna True si tuvo éxito."""
        if cls._connection and not cls._connection.is_closed:
            return True
        try:
            cls._connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL,
                timeout=5,
            )
            cls._channel = await cls._connection.channel()
            cls._exchange = await cls._channel.declare_exchange(
                EXCHANGE_NAME,
                ExchangeType.TOPIC,
                durable=True,
            )
            logger.info(f"MOM Publisher conectado a RabbitMQ: {settings.RABBITMQ_URL}")
            return True
        except Exception as e:
            logger.warning(f"MOM Publisher: No se pudo conectar a RabbitMQ: {e}")
            cls._connection = None
            cls._channel = None
            cls._exchange = None
            return False

    @classmethod
    async def publish(cls, event: BaseEvent, routing_key: str = "") -> bool:
        """
        Publica un evento en el exchange.
        routing_key se genera automáticamente desde event_type si no se pasa.
        Ejemplo: event_type='message.sent' → routing_key='message.sent'
        """
        if not routing_key:
            routing_key = event.event_type

        if cls._exchange is None:
            connected = await cls.connect()
            if not connected:
                logger.warning(
                    f"MOM: Evento '{event.event_type}' descartado (RabbitMQ no disponible)"
                )
                return False

        try:
            message = aio_pika.Message(
                body=event.to_json(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await cls._exchange.publish(message, routing_key=routing_key)
            logger.info(f"MOM Published: [{routing_key}] {event.event_type}")
            return True
        except Exception as e:
            logger.error(f"MOM Publish error: {e}")
            cls._exchange = None  # Forzar reconexión en próximo intento
            return False

    @classmethod
    async def close(cls):
        """Cierra la conexión con RabbitMQ."""
        if cls._connection and not cls._connection.is_closed:
            await cls._connection.close()
            logger.info("MOM Publisher desconectado de RabbitMQ")
        cls._connection = None
        cls._channel = None
        cls._exchange = None
