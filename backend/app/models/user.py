"""User model for authentication and authorization."""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user_session import UserSession


class UserRole(str, Enum):
    """User role enumeration for access control."""

    ANONYMOUS = "anonymous"
    USER = "user"
    UNLIMITED = "unlimited"
    ADMIN = "admin"


class AuthProvider(str, Enum):
    """Authentication provider enumeration."""

    EMAIL = "email"
    GOOGLE = "google"
    GITHUB = "github"
    FACEBOOK = "facebook"


class User(Base, TimestampMixin):
    """
    Represents an authenticated user in the system.

    Users can authenticate via OAuth providers (Google, GitHub, Facebook)
    or email/password. Each user has a role that determines their access level.
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Authentication fields
    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # OAuth provider information
    provider: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AuthProvider.EMAIL.value,
    )

    provider_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    # Profile information
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Authorization
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=UserRole.USER.value,
        index=True,
    )

    # Message limits (nullable = use default from tier)
    message_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # AI context window size (default: 20 messages)
    context_window_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=20,
    )

    # Account status
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Relationships
    auth_sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary for API responses.

        Args:
            include_sensitive: If True, includes email and provider info.
        """
        result = {
            "id": str(self.id),
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "role": self.role,
            "context_window_size": self.context_window_size,
            "is_blocked": self.is_blocked,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if include_sensitive:
            result.update(
                {
                    "email": self.email,
                    "provider": self.provider,
                    "is_email_verified": self.is_email_verified,
                    "message_limit": self.message_limit,
                }
            )

        return result

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN.value

    @property
    def has_unlimited_messages(self) -> bool:
        """Check if user has unlimited message access."""
        return self.role in (UserRole.UNLIMITED.value, UserRole.ADMIN.value)

    def get_effective_message_limit(self) -> int | None:
        """Get the effective message limit for this user.

        Returns:
            Message limit or None if unlimited.
        """
        if self.has_unlimited_messages:
            return None

        if self.message_limit is not None:
            return self.message_limit

        # Default limits by role
        if self.role == UserRole.USER.value:
            return 30
        elif self.role == UserRole.ANONYMOUS.value:
            return 5

        return None
