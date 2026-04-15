"""Presence module – data access layer."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.presence import Presence, PresenceStatus


class PresenceRepository:

    @staticmethod
    async def upsert_online(db: AsyncSession, user_id: UUID) -> Presence:
        result = await db.execute(select(Presence).where(Presence.user_id == user_id))
        presence = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if presence:
            presence.status = PresenceStatus.ONLINE
            presence.last_seen = now
        else:
            presence = Presence(user_id=user_id, status=PresenceStatus.ONLINE, last_seen=now)
            db.add(presence)
        await db.flush()
        await db.refresh(presence)
        return presence

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: UUID) -> Presence | None:
        result = await db.execute(select(Presence).where(Presence.user_id == user_id))
        return result.scalar_one_or_none()
