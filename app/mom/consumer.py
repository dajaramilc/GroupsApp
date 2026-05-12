"""
MOM — Consumer (Consumidor de eventos).

Se suscribe a colas de RabbitMQ y ejecuta callbacks para cada evento recibido.
Diseñado para correr como tarea en background dentro del lifespan de FastAPI.
"""
import asyncio
import logging
from typing import Callable, Awaitable, Optional

import aio_pika
from aio_pika import ExchangeType

from app.core.config import settings

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "groupsapp.events"


class EventConsumer:
    """Consume eventos de RabbitMQ de forma asíncrona."""

    def __init__(self, queue_name: str, routing_keys: list[str]):
        """
        Args:
            queue_name: Nombre de la cola (ej: 'svc-presence.events')
            routing_keys: Lista de routing keys a escuchar (ej: ['message.sent', 'user.#'])
        """
        self.queue_name = queue_name
        self.routing_keys = routing_keys
        self._connection: Optional[aio_pika.abc.AbstractRobustConnection] = None
        self._channel: Optional[aio_pika.abc.AbstractChannel] = None
        self._task: Optional[asyncio.Task] = None

    async def start(self, callback: Callable[[dict], Awaitable[None]]):
        """
        Inicia el consumer en background.
        callback recibe un dict con el evento deserializado.
        """
        self._task = asyncio.create_task(self._consume_loop(callback))
        logger.info(f"MOM Consumer '{self.queue_name}' iniciado (routing: {self.routing_keys})")

    async def _consume_loop(self, callback: Callable[[dict], Awaitable[None]]):
        """Loop de reconexión y consumo."""
        while True:
            try:
                self._connection = await aio_pika.connect_robust(
                    settings.RABBITMQ_URL,
                    timeout=5,
                )
                self._channel = await self._connection.channel()
                await self._channel.set_qos(prefetch_count=10)

                # Declarar exchange y cola
                exchange = await self._channel.declare_exchange(
                    EXCHANGE_NAME,
                    ExchangeType.TOPIC,
                    durable=True,
                )
                queue = await self._channel.declare_queue(
                    self.queue_name,
                    durable=True,
                )

                # Bind cola con routing keys
                for rk in self.routing_keys:
                    await queue.bind(exchange, routing_key=rk)

                logger.info(
                    f"MOM Consumer '{self.queue_name}' conectado y escuchando "
                    f"eventos: {self.routing_keys}"
                )

                # Consumir mensajes
                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        async with message.process():
                            try:
                                import json
                                event_data = json.loads(message.body.decode("utf-8"))
                                logger.info(
                                    f"MOM Consumed: [{message.routing_key}] "
                                    f"{event_data.get('event_type', 'unknown')}"
                                )
                                await callback(event_data)
                            except Exception as e:
                                logger.error(f"MOM Consumer callback error: {e}")

            except asyncio.CancelledError:
                logger.info(f"MOM Consumer '{self.queue_name}' cancelado")
                break
            except Exception as e:
                logger.warning(f"MOM Consumer '{self.queue_name}' error: {e}. Reintentando en 5s...")
                await asyncio.sleep(5)

    async def stop(self):
        """Detiene el consumer."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info(f"MOM Consumer '{self.queue_name}' detenido")
