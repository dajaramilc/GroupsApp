"""Channels module – business logic."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ForbiddenError
from app.models.group import GroupRole
from app.models.user import User
from app.modules.channels.repository import ChannelRepository
from app.modules.channels.schemas import ChannelCreateRequest, ChannelResponse, ChannelListResponse
from app.modules.groups.repository import GroupRepository


class ChannelService:

    @staticmethod
    async def create_channel(
        db: AsyncSession, group_id: UUID, data: ChannelCreateRequest, current_user: User
    ) -> ChannelResponse:
        group = await GroupRepository.get_by_id(db, group_id)
        if not group:
            raise NotFoundError("Group not found")

        member = await GroupRepository.get_member(db, group_id, current_user.id)
        if not member or member.role != GroupRole.ADMIN:
            raise ForbiddenError("Only group admins can create channels")

        channel = await ChannelRepository.create(db, group_id, data.name, data.description, current_user.id)
        return ChannelResponse.model_validate(channel)

    @staticmethod
    async def list_channels(db: AsyncSession, group_id: UUID, current_user: User) -> ChannelListResponse:
        group = await GroupRepository.get_by_id(db, group_id)
        if not group:
            raise NotFoundError("Group not found")

        member = await GroupRepository.get_member(db, group_id, current_user.id)
        if not member:
            raise ForbiddenError("Not a member of this group")

        channels = await ChannelRepository.list_for_group(db, group_id)
        return ChannelListResponse(channels=[ChannelResponse.model_validate(c) for c in channels])

    @staticmethod
    async def get_channel(db: AsyncSession, channel_id: UUID, current_user: User) -> ChannelResponse:
        channel = await ChannelRepository.get_by_id(db, channel_id)
        if not channel:
            raise NotFoundError("Channel not found")

        # Verify user is member of the channel's group
        member = await GroupRepository.get_member(db, channel.group_id, current_user.id)
        if not member:
            raise ForbiddenError("Not a member of the channel's group")

        return ChannelResponse.model_validate(channel)

    @staticmethod
    async def delete_channel(db: AsyncSession, channel_id: UUID, current_user: User) -> None:
        channel = await ChannelRepository.get_by_id(db, channel_id)
        if not channel:
            raise NotFoundError("Channel not found")

        # Verify user is ADMIN of the channel's group
        member = await GroupRepository.get_member(db, channel.group_id, current_user.id)
        if not member or member.role != GroupRole.ADMIN:
            raise ForbiddenError("Only group admins can delete channels")

        await ChannelRepository.delete(db, channel_id)
