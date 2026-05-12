"""Messages module – business logic."""
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ForbiddenError
from app.grpc_clients.channels_client import check_channel_access
from app.models.user import User
from app.modules.channels.repository import ChannelRepository
from app.modules.groups.repository import GroupRepository
from app.modules.messages.repository import MessageRepository
from app.modules.messages.schemas import (
    SendMessageRequest, MessageResponse, MessageListResponse,
    MessageStatusResponse, MessageStatusListResponse,
    ConversationPreviewResponse, ConversationListResponse,
)
from app.modules.users.repository import UserRepository
from app.modules.files.repository import FileRepository
from app.modules.files.schemas import AttachmentResponse
from app.mom.publisher import EventPublisher
from app.mom.events import MessageSentEvent

logger = logging.getLogger(__name__)


class MessageService:

    @staticmethod
    async def _enrich_with_attachments(db: AsyncSession, messages: list, responses: list[MessageResponse]) -> list[MessageResponse]:
        """Bulk-load attachments and inject into MessageResponse objects."""
        msg_ids = [m.id for m in messages]
        att_map = await FileRepository.list_by_message_ids(db, msg_ids)
        for resp in responses:
            raw_atts = att_map.get(resp.id, [])
            resp.attachments = [AttachmentResponse.model_validate(a) for a in raw_atts]
        return responses

    # ── Channel messages ────────────────────────────────

    @staticmethod
    async def send_channel_message(
        db: AsyncSession, channel_id: UUID, data: SendMessageRequest, current_user: User
    ) -> MessageResponse:
        # Verificación de acceso vía gRPC (svc-messages → svc-channels)
        allowed, _group_id, reason = await check_channel_access(channel_id, current_user.id)
        if reason == "grpc_unavailable":
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Channels service (gRPC) is unavailable")
        elif reason == "channel_not_found":
            raise NotFoundError("Channel not found")
        elif not allowed:
            raise ForbiddenError("Not a member of the channel's group")

        msg = await MessageRepository.create_channel_message(db, current_user.id, channel_id, data.content)

        # MOM: Publicar evento asíncrono
        await EventPublisher.publish(MessageSentEvent(
            sender_id=str(current_user.id),
            message_id=str(msg.id),
            message_type="channel",
            target_id=str(channel_id),
            content_preview=data.content[:100],
        ))

        return MessageResponse.model_validate(msg)

    @staticmethod
    async def list_channel_messages(
        db: AsyncSession, channel_id: UUID, current_user: User, skip: int = 0, limit: int = 50
    ) -> MessageListResponse:
        # Verificación de acceso vía gRPC (svc-messages → svc-channels)
        allowed, _group_id, reason = await check_channel_access(channel_id, current_user.id)
        if reason == "grpc_unavailable":
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Channels service (gRPC) is unavailable")
        elif reason == "channel_not_found":
            raise NotFoundError("Channel not found")
        elif not allowed:
            raise ForbiddenError("Not a member of the channel's group")

        messages = await MessageRepository.list_channel_messages(db, channel_id, skip, limit)
        responses = [MessageResponse.model_validate(m) for m in messages]
        await MessageService._enrich_with_attachments(db, messages, responses)
        return MessageListResponse(messages=responses)

    # ── Direct messages ─────────────────────────────────

    @staticmethod
    async def send_direct_message(
        db: AsyncSession, target_user_id: UUID, data: SendMessageRequest, current_user: User
    ) -> MessageResponse:
        if target_user_id == current_user.id:
            raise ForbiddenError("Cannot send messages to yourself")

        # Assume target user exists or check via REST/gRPC. 
        # Cannot check via UserRepository because users table is in auth.db

        # (Restriction removed) Any user can DM any other user

        conv = await MessageRepository.get_or_create_conversation(db, current_user.id, target_user_id)
        msg = await MessageRepository.create_direct_message(db, current_user.id, conv.id, data.content)

        # Create SENT status for recipient
        await MessageRepository.create_sent_status(db, msg.id, target_user_id)

        # MOM: Publicar evento asíncrono
        await EventPublisher.publish(MessageSentEvent(
            sender_id=str(current_user.id),
            message_id=str(msg.id),
            message_type="direct",
            target_id=str(target_user_id),
            content_preview=data.content[:100],
        ))

        resp = MessageResponse.model_validate(msg)
        resp.status = "sent"
        return resp

    @staticmethod
    async def list_direct_messages(
        db: AsyncSession, target_user_id: UUID, current_user: User, skip: int = 0, limit: int = 50
    ) -> MessageListResponse:
        # Assume target user exists

        conv = await MessageRepository.get_or_create_conversation(db, current_user.id, target_user_id)
        messages = await MessageRepository.list_direct_messages(db, conv.id, skip, limit)

        # Mark incoming messages as delivered
        await MessageRepository.mark_delivered_for_user(db, current_user.id)

        # Get statuses for own messages (to show checkmarks)
        own_msg_ids = [m.id for m in messages if m.sender_id == current_user.id]
        statuses = await MessageRepository.get_dm_statuses_bulk(db, own_msg_ids, current_user.id)

        result = []
        for m in messages:
            resp = MessageResponse.model_validate(m)
            if m.sender_id == current_user.id and m.id in statuses:
                resp.status = statuses[m.id].value if hasattr(statuses[m.id], 'value') else str(statuses[m.id])
            result.append(resp)

        await MessageService._enrich_with_attachments(db, messages, result)
        return MessageListResponse(messages=result)

    # ── Audio messages ──────────────────────────────────

    @staticmethod
    async def send_channel_audio(
        db: AsyncSession, channel_id: UUID, current_user: User
    ) -> MessageResponse:
        # Verificación de acceso vía gRPC (svc-messages → svc-channels)
        allowed, _group_id, reason = await check_channel_access(channel_id, current_user.id)
        if reason == "grpc_unavailable":
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Channels service (gRPC) is unavailable")
        elif reason == "channel_not_found":
            raise NotFoundError("Channel not found")
        elif not allowed:
            raise ForbiddenError("Not a member of the channel's group")

        msg = await MessageRepository.create_channel_message(db, current_user.id, channel_id, "🎤 Audio")
        return MessageResponse.model_validate(msg)

    @staticmethod
    async def send_direct_audio(
        db: AsyncSession, target_user_id: UUID, current_user: User
    ) -> MessageResponse:
        if target_user_id == current_user.id:
            raise ForbiddenError("Cannot send messages to yourself")

        # Assume target user exists

        # (Restriction removed) Any user can DM any other user

        conv = await MessageRepository.get_or_create_conversation(db, current_user.id, target_user_id)
        msg = await MessageRepository.create_direct_message(db, current_user.id, conv.id, "🎤 Audio")

        await MessageRepository.create_sent_status(db, msg.id, target_user_id)

        resp = MessageResponse.model_validate(msg)
        resp.status = "sent"
        return resp

    # ── Read status ─────────────────────────────────────

    @staticmethod
    async def mark_as_read(db: AsyncSession, message_id: UUID, current_user: User) -> MessageStatusResponse:
        msg = await MessageRepository.get_by_id(db, message_id)
        if not msg:
            raise NotFoundError("Message not found")

        status = await MessageRepository.mark_as_read(db, message_id, current_user.id)
        return MessageStatusResponse.model_validate(status)

    @staticmethod
    async def get_statuses(db: AsyncSession, message_id: UUID, current_user: User) -> MessageStatusListResponse:
        msg = await MessageRepository.get_by_id(db, message_id)
        if not msg:
            raise NotFoundError("Message not found")

        statuses = await MessageRepository.get_statuses(db, message_id)
        return MessageStatusListResponse(statuses=[MessageStatusResponse.model_validate(s) for s in statuses])

    # ── Conversations ───────────────────────────────────

    @staticmethod
    async def get_recent_conversations(db: AsyncSession, current_user: User) -> ConversationListResponse:
        raw = await MessageRepository.list_recent_conversations(db, current_user.id)
        previews = []
        for item in raw:
            # Cannot fetch user details from UserRepository (auth.db)
            previews.append(ConversationPreviewResponse(
                conversation_id=item["conversation_id"],
                other_user_id=item["other_user_id"],
                display_name="User", # Fallback
                username="user", # Fallback
                last_message=item["last_message"],
                last_message_time=item["last_message_time"],
                sender_id=item["sender_id"],
                unread_count=item["unread_count"],
            ))
        return ConversationListResponse(conversations=previews)
