"""Channels module – Pydantic schemas."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class ChannelCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class ChannelResponse(BaseModel):
    id: UUID
    group_id: UUID
    name: str
    description: str | None
    created_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ChannelListResponse(BaseModel):
    channels: list[ChannelResponse]
