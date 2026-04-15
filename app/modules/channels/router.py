"""Channels module – API routes."""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.modules.channels.schemas import ChannelCreateRequest, ChannelResponse, ChannelListResponse
from app.modules.channels.service import ChannelService

router = APIRouter(tags=["Channels"])


@router.post("/groups/{group_id}/channels", response_model=ChannelResponse, status_code=201)
async def create_channel(
    group_id: UUID,
    data: ChannelCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ChannelService.create_channel(db, group_id, data, current_user)


@router.get("/groups/{group_id}/channels", response_model=ChannelListResponse)
async def list_channels(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ChannelService.list_channels(db, group_id, current_user)


@router.get("/channels/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ChannelService.get_channel(db, channel_id, current_user)


@router.delete("/channels/{channel_id}", status_code=204)
async def delete_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ChannelService.delete_channel(db, channel_id, current_user)
