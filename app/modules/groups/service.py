"""Groups module – business logic."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ForbiddenError, ConflictError
from app.models.group import GroupRole
from app.models.user import User
from app.modules.groups.repository import GroupRepository
from app.modules.groups.schemas import (
    GroupCreateRequest, GroupResponse, GroupListResponse,
    AddMemberRequest, GroupMemberResponse, GroupMemberListResponse,
)
from app.modules.users.repository import UserRepository
from app.modules.channels.repository import ChannelRepository


class GroupService:

    @staticmethod
    async def create_group(db: AsyncSession, data: GroupCreateRequest, current_user: User) -> GroupResponse:
        group = await GroupRepository.create(db, data.name, data.description, current_user.id)
        # Creator becomes admin
        await GroupRepository.add_member(db, group.id, current_user.id, GroupRole.ADMIN)
        # Auto-create #general channel
        await ChannelRepository.create(db, group.id, "general", "Canal general del grupo", current_user.id)
        return GroupResponse.model_validate(group)

    @staticmethod
    async def list_my_groups(db: AsyncSession, current_user: User) -> GroupListResponse:
        groups = await GroupRepository.list_for_user(db, current_user.id)
        return GroupListResponse(groups=[GroupResponse.model_validate(g) for g in groups])

    @staticmethod
    async def get_group(db: AsyncSession, group_id: UUID, current_user: User) -> GroupResponse:
        group = await GroupRepository.get_by_id(db, group_id)
        if not group:
            raise NotFoundError("Group not found")
        # Check membership
        member = await GroupRepository.get_member(db, group_id, current_user.id)
        if not member:
            raise ForbiddenError("Not a member of this group")
        return GroupResponse.model_validate(group)

    @staticmethod
    async def add_member(db: AsyncSession, group_id: UUID, data: AddMemberRequest, current_user: User) -> GroupMemberResponse:
        group = await GroupRepository.get_by_id(db, group_id)
        if not group:
            raise NotFoundError("Group not found")

        # Only admins can add members
        admin_member = await GroupRepository.get_member(db, group_id, current_user.id)
        if not admin_member or admin_member.role != GroupRole.ADMIN:
            raise ForbiddenError("Only group admins can add members")

        # Check target user exists
        target_user = await UserRepository.get_by_id(db, data.user_id)
        if not target_user:
            raise NotFoundError("User not found")

        # Check not already a member
        existing = await GroupRepository.get_member(db, group_id, data.user_id)
        if existing:
            raise ConflictError("User is already a member of this group")

        member = await GroupRepository.add_member(db, group_id, data.user_id)
        return GroupMemberResponse.model_validate(member)

    @staticmethod
    async def list_members(db: AsyncSession, group_id: UUID, current_user: User) -> GroupMemberListResponse:
        group = await GroupRepository.get_by_id(db, group_id)
        if not group:
            raise NotFoundError("Group not found")

        member = await GroupRepository.get_member(db, group_id, current_user.id)
        if not member:
            raise ForbiddenError("Not a member of this group")

        members = await GroupRepository.list_members(db, group_id)
        return GroupMemberListResponse(members=[GroupMemberResponse.model_validate(m) for m in members])

    @staticmethod
    async def delete_group(db: AsyncSession, group_id: UUID, current_user: User) -> None:
        group = await GroupRepository.get_by_id(db, group_id)
        if not group:
            raise NotFoundError("Group not found")

        member = await GroupRepository.get_member(db, group_id, current_user.id)
        if not member or member.role != GroupRole.ADMIN:
            raise ForbiddenError("Only group admins can delete the group")

        await GroupRepository.delete(db, group_id)

    @staticmethod
    async def remove_member(db: AsyncSession, group_id: UUID, user_id: UUID, current_user: User) -> None:
        group = await GroupRepository.get_by_id(db, group_id)
        if not group:
            raise NotFoundError("Group not found")

        # Must be admin to remove someone
        admin_member = await GroupRepository.get_member(db, group_id, current_user.id)
        if not admin_member or admin_member.role != GroupRole.ADMIN:
            raise ForbiddenError("Only group admins can remove members")

        target_member = await GroupRepository.get_member(db, group_id, user_id)
        if not target_member:
            raise NotFoundError("User is not a member of this group")

        # Prevent removing oneself if they are the only admin
        if user_id == current_user.id:
            members = await GroupRepository.list_members(db, group_id)
            admins = [m for m in members if m.role == GroupRole.ADMIN]
            if len(admins) <= 1:
                raise ConflictError("Cannot remove the only admin of the group. Assign a new admin or delete the group.")

        await GroupRepository.remove_member(db, group_id, user_id)
