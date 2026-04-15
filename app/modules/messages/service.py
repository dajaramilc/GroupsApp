"""Messages module – business logic."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ForbiddenError
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
        channel = await ChannelRepository.get_by_id(db, channel_id)
        if not channel:
            raise NotFoundError("Channel not found")

        # Check group membership
        member = await GroupRepository.get_member(db, channel.group_id, current_user.id)
        if not member:
            raise ForbiddenError("Not a member of the channel's group")

        msg = await MessageRepository.create_channel_message(db, current_user.id, channel_id, data.content)
        return MessageResponse.model_validate(msg)

    @staticmethod
    async def list_channel_messages(
        db: AsyncSession, channel_id: UUID, current_user: User, skip: int = 0, limit: int = 50
    ) -> MessageListResponse:
        channel = await ChannelRepository.get_by_id(db, channel_id)
        if not channel:
            raise NotFoundError("Channel not found")

        member = await GroupRepository.get_member(db, channel.group_id, current_user.id)
        if not member:
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

        target = await UserRepository.get_by_id(db, target_user_id)
        if not target:
            raise NotFoundError("User not found")

        # Must share at least one group
        share = await GroupRepository.users_share_group(db, current_user.id, target_user_id)
        if not share:
            raise ForbiddenError("You can only message users you share a group with")

        conv = await MessageRepository.get_or_create_conversation(db, current_user.id, target_user_id)
        msg = await MessageRepository.create_direct_message(db, current_user.id, conv.id, data.content)

        # Create SENT status for recipient
        await MessageRepository.create_sent_status(db, msg.id, target_user_id)

        resp = MessageResponse.model_validate(msg)
        resp.status = "sent"
        return resp

    @staticmethod
    async def list_direct_messages(
        db: AsyncSession, target_user_id: UUID, current_user: User, skip: int = 0, limit: int = 50
    ) -> MessageListResponse:
        target = await UserRepository.get_by_id(db, target_user_id)
        if not target:
            raise NotFoundError("User not found")

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
        channel = await ChannelRepository.get_by_id(db, channel_id)
        if not channel:
            raise NotFoundError("Channel not found")

        member = await GroupRepository.get_member(db, channel.group_id, current_user.id)
        if not member:
            raise ForbiddenError("Not a member of the channel's group")

        msg = await MessageRepository.create_channel_message(db, current_user.id, channel_id, "🎤 Audio")
        return MessageResponse.model_validate(msg)

    @staticmethod
    async def send_direct_audio(
        db: AsyncSession, target_user_id: UUID, current_user: User
    ) -> MessageResponse:
        if target_user_id == current_user.id:
            raise ForbiddenError("Cannot send messages to yourself")

        target = await UserRepository.get_by_id(db, target_user_id)
        if not target:
            raise NotFoundError("User not found")

        share = await GroupRepository.users_share_group(db, current_user.id, target_user_id)
        if not share:
            raise ForbiddenError("You can only message users you share a group with")

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
            user = await UserRepository.get_by_id(db, item["other_user_id"])
            if not user:
                continue
            previews.append(ConversationPreviewResponse(
                conversation_id=item["conversation_id"],
                other_user_id=item["other_user_id"],
                display_name=user.display_name,
                username=user.username,
                last_message=item["last_message"],
                last_message_time=item["last_message_time"],
                sender_id=item["sender_id"],
                unread_count=item["unread_count"],
            ))
        return ConversationListResponse(conversations=previews)
