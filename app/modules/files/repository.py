"""Files module – data access layer."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import MessageAttachment


class FileRepository:

    @staticmethod
    async def create_attachment(
        db: AsyncSession,
        message_id: UUID,
        filename: str,
        original_filename: str,
        content_type: str,
        file_size: int,
        storage_path: str,
    ) -> MessageAttachment:
        att = MessageAttachment(
            message_id=message_id,
            filename=filename,
            original_filename=original_filename,
            content_type=content_type,
            file_size=file_size,
            storage_path=storage_path,
        )
        db.add(att)
        await db.flush()
        await db.refresh(att)
        return att

    @staticmethod
    async def get_by_id(db: AsyncSession, attachment_id: UUID) -> MessageAttachment | None:
        result = await db.execute(select(MessageAttachment).where(MessageAttachment.id == attachment_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_message_id(db: AsyncSession, message_id: UUID) -> list[MessageAttachment]:
        result = await db.execute(
            select(MessageAttachment).where(MessageAttachment.message_id == message_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_by_message_ids(db: AsyncSession, message_ids: list[UUID]) -> dict[UUID, list[MessageAttachment]]:
        """Return {message_id: [attachments]} for a list of message IDs."""
        if not message_ids:
            return {}
        result = await db.execute(
            select(MessageAttachment).where(MessageAttachment.message_id.in_(message_ids))
        )
        attachments = list(result.scalars().all())
        mapping: dict[UUID, list[MessageAttachment]] = {}
        for att in attachments:
            mapping.setdefault(att.message_id, []).append(att)
        return mapping
