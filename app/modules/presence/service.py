"""Presence module – business logic."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.presence import PresenceStatus
from app.models.user import User
from app.modules.presence.repository import PresenceRepository
from app.modules.presence.schemas import PresenceResponse


class PresenceService:

    @staticmethod
    async def heartbeat(db: AsyncSession, current_user: User) -> PresenceResponse:
        presence = await PresenceRepository.upsert_online(db, current_user.id)
        return PresenceResponse.model_validate(presence)

    @staticmethod
    async def get_presence(db: AsyncSession, user_id: UUID) -> PresenceResponse:
        presence = await PresenceRepository.get_by_user(db, user_id)
        if not presence:
            return PresenceResponse(
                user_id=user_id,
                status=PresenceStatus.OFFLINE,
                last_seen=datetime.now(timezone.utc),
            )

        # Auto-offline if last_seen is too old
        timeout = timedelta(seconds=settings.PRESENCE_TIMEOUT_SECONDS)
        if presence.last_seen < datetime.now(timezone.utc) - timeout:
            return PresenceResponse(
                user_id=user_id,
                status=PresenceStatus.OFFLINE,
                last_seen=presence.last_seen,
            )

        return PresenceResponse.model_validate(presence)
