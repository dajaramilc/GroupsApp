"""Users module – data access layer."""
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: UUID) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def search(db: AsyncSession, query: str, limit: int = 20) -> list[User]:
        pattern = f"%{query}%"
        result = await db.execute(
            select(User)
            .where(or_(User.username.ilike(pattern), User.display_name.ilike(pattern)))
            .limit(limit)
        )
        return list(result.scalars().all())
