"""Files module – Pydantic schemas."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: UUID
    message_id: UUID
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}
