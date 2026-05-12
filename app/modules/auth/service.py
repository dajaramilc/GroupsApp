"""Auth module – business logic."""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, BadRequestError
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.modules.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.mom.publisher import EventPublisher
from app.mom.events import UserRegisteredEvent

logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    async def register(db: AsyncSession, data: RegisterRequest) -> UserResponse:
        # Check duplicates
        existing = await db.execute(
            select(User).where((User.username == data.username) | (User.email == data.email))
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Username or email already exists")

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            display_name=data.display_name,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

        # MOM: Publicar evento de registro
        await EventPublisher.publish(UserRegisteredEvent(
            user_id=str(user.id),
            username=user.username,
            email=user.email,
        ))

        return UserResponse.model_validate(user)

    @staticmethod
    async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
        result = await db.execute(select(User).where(User.username == data.username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(data.password, user.hashed_password):
            raise BadRequestError("Invalid username or password")
        if not user.is_active:
            raise BadRequestError("User account is deactivated")

        token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=token)
