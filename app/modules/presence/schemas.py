"""Presence module – Pydantic schemas."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class PresenceResponse(BaseModel):
    user_id: UUID
    status: str
    last_seen: datetime

    model_config = {"from_attributes": True}
