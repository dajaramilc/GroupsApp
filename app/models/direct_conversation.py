"""DirectConversation model – canonical pair for 1-to-1 DMs."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DirectConversation(Base):
    """
    Represents a 1-to-1 conversation between two users.
    user1_id is always the lesser UUID (lexicographically) to avoid duplicates.
    """
    __tablename__ = "direct_conversations"
    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_direct_conversation_pair"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user1_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user2_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
