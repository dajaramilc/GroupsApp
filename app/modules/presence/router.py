"""Presence module – API routes."""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.modules.presence.schemas import PresenceResponse
from app.modules.presence.service import PresenceService

router = APIRouter(tags=["Presence"])


@router.post("/presence/heartbeat", response_model=PresenceResponse)
async def heartbeat(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await PresenceService.heartbeat(db, current_user)


@router.get("/users/{user_id}/presence", response_model=PresenceResponse)
async def get_presence(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return await PresenceService.get_presence(db, user_id)
