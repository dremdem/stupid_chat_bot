"""Message model for storing chat messages."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.session import ChatSession


class Message(Base, TimestampMixin):
    """
    Represents a single message in a chat session.

    Stores messages from both users and AI assistant.
    """

    __tablename__ = "messages"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Foreign key to session
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message content
    sender: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # 'user' or 'assistant'

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Flexible metadata storage (e.g., {"provider": "anthropic", "model": "claude-3-5-sonnet"})
    meta: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        """String representation of the message."""
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, sender={self.sender}, content={preview})>"

    def to_dict(self) -> dict:
        """Convert message to dictionary for API responses."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "sender": self.sender,
            "content": self.content,
            "metadata": self.meta,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
