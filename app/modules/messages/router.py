"""Messages module – API routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.modules.messages.schemas import (
    SendMessageRequest, MessageResponse, MessageListResponse,
    MessageStatusResponse, MessageStatusListResponse,
    ConversationListResponse,
)
from app.modules.messages.service import MessageService
from app.modules.files.service import FileService

router = APIRouter(tags=["Messages"])


# ── Channel messages ────────────────────────────────────

@router.post("/channels/{channel_id}/messages", response_model=MessageResponse, status_code=201)
async def send_channel_message(
    channel_id: UUID,
    data: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await MessageService.send_channel_message(db, channel_id, data, current_user)


@router.get("/channels/{channel_id}/messages", response_model=MessageListResponse)
async def list_channel_messages(
    channel_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await MessageService.list_channel_messages(db, channel_id, current_user, skip, limit)


# ── Direct messages ─────────────────────────────────────

@router.post("/users/{user_id}/messages", response_model=MessageResponse, status_code=201)
async def send_direct_message(
    user_id: UUID,
    data: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await MessageService.send_direct_message(db, user_id, data, current_user)


@router.get("/users/{user_id}/messages", response_model=MessageListResponse)
async def list_direct_messages(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await MessageService.list_direct_messages(db, user_id, current_user, skip, limit)


# ── Audio messages ──────────────────────────────────────

@router.post("/channels/{channel_id}/messages/audio", response_model=MessageResponse, status_code=201)
async def send_channel_audio(
    channel_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg_resp = await MessageService.send_channel_audio(db, channel_id, current_user)
    # Attach audio file
    await FileService.upload_attachment(db, msg_resp.id, file)
    return msg_resp


@router.post("/users/{user_id}/messages/audio", response_model=MessageResponse, status_code=201)
async def send_direct_audio(
    user_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg_resp = await MessageService.send_direct_audio(db, user_id, current_user)
    await FileService.upload_attachment(db, msg_resp.id, file)
    return msg_resp


# ── Read status ─────────────────────────────────────────

@router.post("/messages/{message_id}/read", response_model=MessageStatusResponse, status_code=200)
async def mark_as_read(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await MessageService.mark_as_read(db, message_id, current_user)


@router.get("/messages/{message_id}/status", response_model=MessageStatusListResponse)
async def get_message_status(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await MessageService.get_statuses(db, message_id, current_user)


# ── Conversations (chat history) ────────────────────────

@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await MessageService.get_recent_conversations(db, current_user)
