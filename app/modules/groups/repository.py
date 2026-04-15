"""Groups module – data access layer."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group, GroupMember, GroupRole


class GroupRepository:

    @staticmethod
    async def create(db: AsyncSession, name: str, description: str | None, created_by: UUID) -> Group:
        group = Group(name=name, description=description, created_by=created_by)
        db.add(group)
        await db.flush()
        await db.refresh(group)
        return group

    @staticmethod
    async def get_by_id(db: AsyncSession, group_id: UUID) -> Group | None:
        result = await db.execute(select(Group).where(Group.id == group_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_for_user(db: AsyncSession, user_id: UUID) -> list[Group]:
        result = await db.execute(
            select(Group)
            .join(GroupMember, GroupMember.group_id == Group.id)
            .where(GroupMember.user_id == user_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def add_member(db: AsyncSession, group_id: UUID, user_id: UUID, role: GroupRole = GroupRole.MEMBER) -> GroupMember:
        member = GroupMember(group_id=group_id, user_id=user_id, role=role)
        db.add(member)
        await db.flush()
        await db.refresh(member)
        return member

    @staticmethod
    async def get_member(db: AsyncSession, group_id: UUID, user_id: UUID) -> GroupMember | None:
        result = await db.execute(
            select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_members(db: AsyncSession, group_id: UUID) -> list[GroupMember]:
        result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_id))
        return list(result.scalars().all())

    @staticmethod
    async def users_share_group(db: AsyncSession, user1_id: UUID, user2_id: UUID) -> bool:
        """Check if two users share at least one group."""
        from sqlalchemy import and_
        gm1 = GroupMember.__table__.alias("gm1")
        gm2 = GroupMember.__table__.alias("gm2")
        result = await db.execute(
            select(gm1.c.group_id)
            .join(gm2, and_(gm1.c.group_id == gm2.c.group_id))
            .where(gm1.c.user_id == user1_id, gm2.c.user_id == user2_id)
            .limit(1)
        )
        return result.first() is not None

    @staticmethod
    async def delete(db: AsyncSession, group_id: UUID) -> bool:
        result = await db.execute(select(Group).where(Group.id == group_id))
        group = result.scalar_one_or_none()
        if not group:
            return False
        await db.delete(group)
        await db.flush()
        return True

    @staticmethod
    async def remove_member(db: AsyncSession, group_id: UUID, user_id: UUID) -> bool:
        result = await db.execute(
            select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()
        if not member:
            return False
        await db.delete(member)
        await db.flush()
        return True
