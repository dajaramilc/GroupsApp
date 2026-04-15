"""Users module – business logic."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserProfileResponse, UserSearchResponse


class UserService:

    @staticmethod
    async def get_profile(db: AsyncSession, user_id: UUID) -> UserProfileResponse:
        user = await UserRepository.get_by_id(db, user_id)
        if not user:
            raise NotFoundError("User not found")
        return UserProfileResponse.model_validate(user)

    @staticmethod
    async def search_users(db: AsyncSession, query: str) -> UserSearchResponse:
        users = await UserRepository.search(db, query)
        return UserSearchResponse(users=[UserProfileResponse.model_validate(u) for u in users])
