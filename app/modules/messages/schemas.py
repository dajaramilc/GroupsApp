"""Messages module – Pydantic schemas."""
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.modules.files.schemas import AttachmentResponse


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    id: UUID
    sender_id: UUID
    channel_id: UUID | None
    conversation_id: UUID | None
    content: str
    message_type: str
    created_at: datetime
    status: Optional[str] = None  # sent / delivered / read (for own DM messages)
    attachments: List[AttachmentResponse] = []

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]


class MarkReadRequest(BaseModel):
    pass  # No body needed, just calling the endpoint


class MessageStatusResponse(BaseModel):
    id: UUID
    message_id: UUID
    user_id: UUID
    status: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageStatusListResponse(BaseModel):
    statuses: list[MessageStatusResponse]


class ConversationPreviewResponse(BaseModel):
    conversation_id: UUID
    other_user_id: UUID
    display_name: str
    username: str
    last_message: str
    last_message_time: datetime
    sender_id: UUID
    unread_count: int


class ConversationListResponse(BaseModel):
    conversations: list[ConversationPreviewResponse]

