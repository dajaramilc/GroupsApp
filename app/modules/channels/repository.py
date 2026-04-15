"""Channels module – data access layer."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import Channel


class ChannelRepository:

    @staticmethod
    async def create(db: AsyncSession, group_id: UUID, name: str, description: str | None, created_by: UUID) -> Channel:
        channel = Channel(group_id=group_id, name=name, description=description, created_by=created_by)
        db.add(channel)
        await db.flush()
        await db.refresh(channel)
        return channel

    @staticmethod
    async def get_by_id(db: AsyncSession, channel_id: UUID) -> Channel | None:
        result = await db.execute(select(Channel).where(Channel.id == channel_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_for_group(db: AsyncSession, group_id: UUID) -> list[Channel]:
        result = await db.execute(select(Channel).where(Channel.group_id == group_id))
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, channel_id: UUID) -> bool:
        result = await db.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalar_one_or_none()
        if not channel:
            return False
        await db.delete(channel)
        await db.flush()
        return True
