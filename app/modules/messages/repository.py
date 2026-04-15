"""Messages module – data access layer."""
from uuid import UUID

from sqlalchemy import select, update, and_, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.direct_conversation import DirectConversation
from app.models.message import Message, MessageType
from app.models.message_status import MessageStatus, DeliveryStatus


class MessageRepository:

    # ── Channel messages ────────────────────────────────

    @staticmethod
    async def create_channel_message(
        db: AsyncSession, sender_id: UUID, channel_id: UUID, content: str
    ) -> Message:
        msg = Message(
            sender_id=sender_id,
            channel_id=channel_id,
            content=content,
            message_type=MessageType.CHANNEL,
        )
        db.add(msg)
        await db.flush()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def list_channel_messages(
        db: AsyncSession, channel_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.channel_id == channel_id)
            .order_by(Message.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Direct messages ─────────────────────────────────

    @staticmethod
    async def get_or_create_conversation(
        db: AsyncSession, user1_id: UUID, user2_id: UUID
    ) -> DirectConversation:
        # Ensure canonical order
        low, high = sorted([user1_id, user2_id])
        result = await db.execute(
            select(DirectConversation).where(
                DirectConversation.user1_id == low,
                DirectConversation.user2_id == high,
            )
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv

        conv = DirectConversation(user1_id=low, user2_id=high)
        db.add(conv)
        await db.flush()
        await db.refresh(conv)
        return conv

    @staticmethod
    async def create_direct_message(
        db: AsyncSession, sender_id: UUID, conversation_id: UUID, content: str
    ) -> Message:
        msg = Message(
            sender_id=sender_id,
            conversation_id=conversation_id,
            content=content,
            message_type=MessageType.DIRECT,
        )
        db.add(msg)
        await db.flush()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def list_direct_messages(
        db: AsyncSession, conversation_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Message get ─────────────────────────────────────

    @staticmethod
    async def get_by_id(db: AsyncSession, message_id: UUID) -> Message | None:
        result = await db.execute(select(Message).where(Message.id == message_id))
        return result.scalar_one_or_none()

    # ── Read status ─────────────────────────────────────

    @staticmethod
    async def mark_as_read(db: AsyncSession, message_id: UUID, user_id: UUID) -> MessageStatus:
        result = await db.execute(
            select(MessageStatus).where(
                MessageStatus.message_id == message_id,
                MessageStatus.user_id == user_id,
            )
        )
        status = result.scalar_one_or_none()
        if status:
            status.status = DeliveryStatus.READ
        else:
            status = MessageStatus(
                message_id=message_id,
                user_id=user_id,
                status=DeliveryStatus.READ,
            )
            db.add(status)
        await db.flush()
        await db.refresh(status)
        return status

    @staticmethod
    async def get_statuses(db: AsyncSession, message_id: UUID) -> list[MessageStatus]:
        result = await db.execute(
            select(MessageStatus).where(MessageStatus.message_id == message_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_sent_status(db: AsyncSession, message_id: UUID, recipient_id: UUID) -> MessageStatus:
        """Create a SENT status for the recipient when a message is created."""
        status = MessageStatus(
            message_id=message_id,
            user_id=recipient_id,
            status=DeliveryStatus.SENT,
        )
        db.add(status)
        await db.flush()
        await db.refresh(status)
        return status

    @staticmethod
    async def mark_delivered_for_user(db: AsyncSession, user_id: UUID) -> int:
        """Mark all SENT messages for this user as DELIVERED. Returns count updated."""
        result = await db.execute(
            update(MessageStatus)
            .where(
                MessageStatus.user_id == user_id,
                MessageStatus.status == DeliveryStatus.SENT,
            )
            .values(status=DeliveryStatus.DELIVERED)
        )
        await db.flush()
        return result.rowcount

    @staticmethod
    async def get_status_for_user(db: AsyncSession, message_id: UUID, user_id: UUID) -> MessageStatus | None:
        """Get the status of a single message for a specific user."""
        result = await db.execute(
            select(MessageStatus).where(
                MessageStatus.message_id == message_id,
                MessageStatus.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_dm_statuses_bulk(db: AsyncSession, message_ids: list[UUID], viewer_id: UUID) -> dict:
        """For a list of message IDs, return {message_id: status_string} for recipient statuses."""
        if not message_ids:
            return {}
        result = await db.execute(
            select(MessageStatus.message_id, MessageStatus.status)
            .where(
                MessageStatus.message_id.in_(message_ids),
                MessageStatus.user_id != viewer_id,
            )
        )
        return {row.message_id: row.status for row in result.all()}

    @staticmethod
    async def list_recent_conversations(db: AsyncSession, user_id: UUID) -> list[dict]:
        """Returns recent conversations for a user with the latest message."""
        # Get all conversations for this user
        convs = await db.execute(
            select(DirectConversation).where(
                (DirectConversation.user1_id == user_id) | (DirectConversation.user2_id == user_id)
            )
        )
        conversations = list(convs.scalars().all())
        results = []
        for conv in conversations:
            # Get latest message
            msg_result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conv.id)
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            last_msg = msg_result.scalar_one_or_none()
            if not last_msg:
                continue
            # Get unread count
            unread_result = await db.execute(
                select(func.count())
                .select_from(Message)
                .outerjoin(
                    MessageStatus,
                    and_(
                        MessageStatus.message_id == Message.id,
                        MessageStatus.user_id == user_id,
                    )
                )
                .where(
                    Message.conversation_id == conv.id,
                    Message.sender_id != user_id,
                    (MessageStatus.status.is_(None)) | (MessageStatus.status != DeliveryStatus.READ),
                )
            )
            unread_count = unread_result.scalar() or 0
            other_user_id = conv.user2_id if conv.user1_id == user_id else conv.user1_id
            results.append({
                "conversation_id": conv.id,
                "other_user_id": other_user_id,
                "last_message": last_msg.content,
                "last_message_time": last_msg.created_at,
                "sender_id": last_msg.sender_id,
                "unread_count": unread_count,
            })
        # Sort by most recent
        results.sort(key=lambda x: x["last_message_time"], reverse=True)
        return results
