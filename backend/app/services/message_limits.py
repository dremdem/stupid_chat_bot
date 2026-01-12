"""Message limits service for tracking and enforcing message quotas."""

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

# Default limits by user tier
DEFAULT_LIMITS = {
    UserRole.ANONYMOUS.value: 5,
    UserRole.USER.value: 50,  # Authenticated users get 50 messages
    UserRole.UNLIMITED.value: None,  # Unlimited
    UserRole.ADMIN.value: None,  # Unlimited
}


@dataclass
class MessageLimitInfo:
    """Information about a user's message limits."""

    limit: int | None  # None means unlimited
    used: int
    remaining: int | None  # None means unlimited
    is_unlimited: bool
    can_send: bool
    user_role: str
    requires_verification: bool = False  # True if email verification needed

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "limit": self.limit,
            "used": self.used,
            "remaining": self.remaining,
            "is_unlimited": self.is_unlimited,
            "can_send": self.can_send,
            "user_role": self.user_role,
            "requires_verification": self.requires_verification,
        }


class MessageLimitsService:
    """Service for tracking and enforcing message limits."""

    def __init__(self, db: AsyncSession):
        """Initialize the service with a database session."""
        self.db = db

    async def count_user_messages(
        self,
        cookie_user_id: str | None = None,
        auth_user_id: UUID | None = None,
    ) -> int:
        """
        Count total messages sent by a user.

        Counts only user messages (not assistant responses).
        Can count by either cookie-based user_id or authenticated user_id.

        Args:
            cookie_user_id: Cookie-based user identifier (anonymous users)
            auth_user_id: Authenticated user UUID

        Returns:
            Total count of user messages
        """
        from app.models.session import ChatSession

        if auth_user_id:
            # Count messages linked to authenticated user
            query = select(func.count(Message.id)).where(
                Message.user_id == auth_user_id,
                Message.sender == "user",
            )
        elif cookie_user_id:
            # Count messages in sessions owned by cookie user
            query = (
                select(func.count(Message.id))
                .join(ChatSession, Message.session_id == ChatSession.id)
                .where(
                    ChatSession.user_id == cookie_user_id,
                    Message.sender == "user",
                )
            )
        else:
            return 0

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_user_limit(
        self,
        auth_user_id: UUID | None = None,
    ) -> tuple[int | None, str, bool]:
        """
        Get the message limit for a user.

        Args:
            auth_user_id: Authenticated user UUID (None for anonymous)

        Returns:
            Tuple of (limit, role, requires_verification) where limit is None for unlimited
        """
        if auth_user_id:
            # Get authenticated user's limit
            query = select(User).where(User.id == auth_user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if user:
                if user.is_blocked:
                    return 0, user.role, False  # Blocked users can't send

                # Check if email user needs verification
                if user.provider == "email" and not user.is_email_verified:
                    return 0, user.role, True  # Unverified email users can't send

                # Use custom limit if set, otherwise default for role
                if user.message_limit is not None:
                    return user.message_limit, user.role, False

                return DEFAULT_LIMITS.get(user.role), user.role, False

        # Anonymous user
        return DEFAULT_LIMITS[UserRole.ANONYMOUS.value], UserRole.ANONYMOUS.value, False

    async def get_limit_info(
        self,
        cookie_user_id: str | None = None,
        auth_user_id: UUID | None = None,
    ) -> MessageLimitInfo:
        """
        Get complete message limit information for a user.

        Args:
            cookie_user_id: Cookie-based user identifier
            auth_user_id: Authenticated user UUID

        Returns:
            MessageLimitInfo with all limit details
        """
        # Get limit, role, and verification status
        limit, role, requires_verification = await self.get_user_limit(auth_user_id)

        # Count used messages
        used = await self.count_user_messages(
            cookie_user_id=cookie_user_id,
            auth_user_id=auth_user_id,
        )

        # Calculate remaining
        is_unlimited = limit is None
        if is_unlimited:
            remaining = None
            can_send = True
        else:
            remaining = max(0, limit - used)
            can_send = remaining > 0

        # If verification required, can't send regardless of limit
        if requires_verification:
            can_send = False

        return MessageLimitInfo(
            limit=limit,
            used=used,
            remaining=remaining,
            is_unlimited=is_unlimited,
            can_send=can_send,
            user_role=role,
            requires_verification=requires_verification,
        )

    async def check_can_send(
        self,
        cookie_user_id: str | None = None,
        auth_user_id: UUID | None = None,
    ) -> tuple[bool, MessageLimitInfo]:
        """
        Check if a user can send a message.

        Args:
            cookie_user_id: Cookie-based user identifier
            auth_user_id: Authenticated user UUID

        Returns:
            Tuple of (can_send, limit_info)
        """
        limit_info = await self.get_limit_info(
            cookie_user_id=cookie_user_id,
            auth_user_id=auth_user_id,
        )

        if not limit_info.can_send:
            logger.info(
                f"Message limit reached for user "
                f"(cookie={cookie_user_id}, auth={auth_user_id}): "
                f"{limit_info.used}/{limit_info.limit}"
            )

        return limit_info.can_send, limit_info


# Singleton-style function for easy access
async def get_message_limits_service(db: AsyncSession) -> MessageLimitsService:
    """Get a MessageLimitsService instance."""
    return MessageLimitsService(db)
