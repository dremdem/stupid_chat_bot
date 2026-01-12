"""Email verification token model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class EmailVerificationToken(Base, TimestampMixin):
    """
    Stores email verification tokens for users.

    Tokens are hashed (SHA-256) for security. Each user can have multiple
    tokens, but only the most recent one is valid.
    """

    __tablename__ = "email_verification_tokens"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Hashed token (SHA-256)
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    # Expiration time
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Whether token has been used
    is_used: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    # Relationship to user
    user = relationship("User", backref="verification_tokens")

    def __repr__(self) -> str:
        """String representation."""
        return f"<EmailVerificationToken(id={self.id}, user_id={self.user_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.is_expired and not self.is_used
