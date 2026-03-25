"""Users module – Pydantic schemas."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    id: UUID
    username: str
    display_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserSearchResponse(BaseModel):
    users: list[UserProfileResponse]
