"""ChatSession model for storing conversation sessions."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.message import Message


class ChatSession(Base, TimestampMixin):
    """
    Represents a chat conversation session.

    Each session belongs to a specific user (identified by user_id cookie).
    Users can have multiple sessions, each with its own conversation history.
    """

    __tablename__ = "chat_sessions"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # User identification (from cookie)
    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,  # Creates index ix_chat_sessions_user_id
    )

    # Session metadata
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="Default Chat Session",
    )

    # Flexible metadata storage (e.g., {"is_default": true, "theme": "dark"})
    meta: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        """String representation of the session."""
        return f"<ChatSession(id={self.id}, title={self.title})>"

    def to_dict(self, include_message_count: bool = False) -> dict:
        """Convert session to dictionary for API responses.

        Args:
            include_message_count: If True, includes message count (requires loaded messages).
        """
        result = {
            "id": str(self.id),
            "title": self.title,
            "metadata": self.meta,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        # Only include message count if explicitly requested and messages are loaded
        if include_message_count:
            try:
                result["message_count"] = len(self.messages)
            except Exception:
                result["message_count"] = 0

        return result
