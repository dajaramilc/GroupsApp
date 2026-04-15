"""Groups module – Pydantic schemas."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class GroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class GroupResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class GroupListResponse(BaseModel):
    groups: list[GroupResponse]


class AddMemberRequest(BaseModel):
    user_id: UUID


class GroupMemberResponse(BaseModel):
    id: UUID
    group_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class GroupMemberListResponse(BaseModel):
    members: list[GroupMemberResponse]
