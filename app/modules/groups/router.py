"""Groups module – API routes."""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.modules.groups.schemas import (
    GroupCreateRequest, GroupResponse, GroupListResponse,
    AddMemberRequest, GroupMemberResponse, GroupMemberListResponse,
)
from app.modules.groups.service import GroupService

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("", response_model=GroupResponse, status_code=201)
async def create_group(
    data: GroupCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await GroupService.create_group(db, data, current_user)


@router.get("", response_model=GroupListResponse)
async def list_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await GroupService.list_my_groups(db, current_user)


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await GroupService.get_group(db, group_id, current_user)


@router.post("/{group_id}/members", response_model=GroupMemberResponse, status_code=201)
async def add_member(
    group_id: UUID,
    data: AddMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await GroupService.add_member(db, group_id, data, current_user)


@router.get("/{group_id}/members", response_model=GroupMemberListResponse)
async def list_members(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await GroupService.list_members(db, group_id, current_user)


@router.delete("/{group_id}", status_code=204)
async def delete_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await GroupService.delete_group(db, group_id, current_user)


@router.delete("/{group_id}/members/{user_id}", status_code=204)
async def remove_member(
    group_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await GroupService.remove_member(db, group_id, user_id, current_user)
