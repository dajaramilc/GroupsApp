"""Users module – API routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.modules.users.schemas import UserProfileResponse, UserSearchResponse
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/search", response_model=UserSearchResponse)
async def search_users(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return await UserService.search_users(db, q)


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return await UserService.get_profile(db, user_id)
