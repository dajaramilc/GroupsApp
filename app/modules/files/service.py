"""Files module – business logic."""
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError, BadRequestError
from app.models.attachment import MessageAttachment
from app.modules.files.repository import FileRepository
from app.modules.files.schemas import AttachmentResponse
from app.modules.files.storage import storage_backend
from app.modules.messages.repository import MessageRepository


class FileService:

    @staticmethod
    async def upload_attachment(
        db: AsyncSession, message_id: UUID, file: UploadFile
    ) -> AttachmentResponse:
        # Verify message exists
        msg = await MessageRepository.get_by_id(db, message_id)
        if not msg:
            raise NotFoundError("Message not found")

        # Read file data
        file_data = await file.read()
        file_size = len(file_data)
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_size:
            raise BadRequestError(f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB")

        original_filename = file.filename or "unnamed"
        content_type = file.content_type or "application/octet-stream"

        # Store file
        storage_path = await storage_backend.save(file_data, original_filename)

        # Save DB record
        att = await FileRepository.create_attachment(
            db,
            message_id=message_id,
            filename=storage_path,
            original_filename=original_filename,
            content_type=content_type,
            file_size=file_size,
            storage_path=storage_path,
        )
        return AttachmentResponse.model_validate(att)

    @staticmethod
    async def get_attachment(db: AsyncSession, attachment_id: UUID) -> tuple[MessageAttachment, bytes]:
        att = await FileRepository.get_by_id(db, attachment_id)
        if not att:
            raise NotFoundError("Attachment not found")

        file_data = await storage_backend.read(att.storage_path)
        return att, file_data

    @staticmethod
    async def list_attachments(db: AsyncSession, message_id: UUID) -> list[AttachmentResponse]:
        atts = await FileRepository.list_by_message_id(db, message_id)
        return [AttachmentResponse.model_validate(a) for a in atts]

    @staticmethod
    async def list_attachments_bulk(db: AsyncSession, message_ids: list[UUID]) -> dict[str, list[AttachmentResponse]]:
        mapping = await FileRepository.list_by_message_ids(db, message_ids)
        return {
            str(mid): [AttachmentResponse.model_validate(a) for a in atts]
            for mid, atts in mapping.items()
        }

