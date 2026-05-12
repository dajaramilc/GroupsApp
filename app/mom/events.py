"""
MOM (Message-Oriented Middleware) — Event Definitions.

Define los eventos que se intercambian entre microservicios a través de RabbitMQ.
Cada evento es un mensaje JSON serializable con un tipo y payload.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional
import json


@dataclass
class BaseEvent:
    """Clase base para todos los eventos del MOM."""
    event_type: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_json(self) -> bytes:
        return json.dumps(asdict(self)).encode("utf-8")

    @classmethod
    def from_json(cls, data: bytes) -> dict:
        return json.loads(data.decode("utf-8"))


@dataclass
class MessageSentEvent(BaseEvent):
    """Emitido por svc-messages cuando se envía un mensaje (DM o canal)."""
    event_type: str = "message.sent"
    sender_id: str = ""
    message_id: str = ""
    message_type: str = ""  # "direct" | "channel"
    target_id: str = ""     # user_id (DM) o channel_id (canal)
    content_preview: str = ""


@dataclass
class UserRegisteredEvent(BaseEvent):
    """Emitido por svc-auth cuando se registra un nuevo usuario."""
    event_type: str = "user.registered"
    user_id: str = ""
    username: str = ""
    email: str = ""


@dataclass
class GroupCreatedEvent(BaseEvent):
    """Emitido por svc-groups cuando se crea un grupo."""
    event_type: str = "group.created"
    group_id: str = ""
    name: str = ""
    description: str = ""
    creator_id: str = ""


@dataclass
class GroupMemberAddedEvent(BaseEvent):
    """Emitido por svc-groups cuando se añade un miembro."""
    event_type: str = "group.member.added"
    group_id: str = ""
    user_id: str = ""
    role: str = ""


@dataclass
class UserPresenceEvent(BaseEvent):
    """Emitido por svc-presence cuando cambia el estado de un usuario."""
    event_type: str = "user.presence_changed"
    user_id: str = ""
    status: str = ""  # "online" | "offline"
