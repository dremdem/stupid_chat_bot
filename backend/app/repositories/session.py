"""Repository for ChatSession operations."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.session import ChatSession
from app.repositories.base import BaseRepository

# Default session identifier - used for the single global session per user
DEFAULT_SESSION_TITLE = "Default Chat Session"
DEFAULT_SESSION_META = {"is_default": True}


class SessionRepository(BaseRepository[ChatSession]):
    """
    Repository for ChatSession database operations.

    Extends BaseRepository with session-specific methods.
    All operations are scoped to a specific user via user_id.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        super().__init__(ChatSession, session)

    async def get_or_create_default(self, user_id: str) -> ChatSession:
        """
        Get the default session for a user, creating it if it doesn't exist.

        Each user has their own default session for initial conversations.

        Args:
            user_id: The user's unique identifier (from cookie)

        Returns:
            The default ChatSession instance for this user
        """
        # Try to find existing default session for this user
        result = await self.session.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .where(ChatSession.meta["is_default"].as_boolean().is_(True))
            .order_by(ChatSession.created_at)
            .limit(1)
        )
        default_session = result.scalars().first()

        if default_session is not None:
            return default_session

        # Create default session for this user
        return await self.create(
            user_id=user_id,
            title=DEFAULT_SESSION_TITLE,
            meta=DEFAULT_SESSION_META,
        )

    async def get_with_messages(
        self,
        session_id: uuid.UUID,
        user_id: str | None = None,
        message_limit: int | None = None,
    ) -> ChatSession | None:
        """
        Get a session with its messages eagerly loaded.

        Args:
            session_id: UUID of the session
            user_id: Optional user_id to validate ownership
            message_limit: Optional limit on number of messages to load

        Returns:
            ChatSession with messages loaded, or None if not found
        """
        query = select(ChatSession).where(ChatSession.id == session_id)

        # Validate user ownership if user_id provided
        if user_id is not None:
            query = query.where(ChatSession.user_id == user_id)

        # Eagerly load messages
        query = query.options(selectinload(ChatSession.messages))

        result = await self.session.execute(query)
        session = result.scalar_one_or_none()

        # Apply message limit in Python (SQLAlchemy doesn't support LIMIT on relationships)
        if session is not None and message_limit is not None:
            # Messages are ordered by created_at in the relationship
            session.messages = session.messages[-message_limit:]

        return session

    async def get_default_with_messages(
        self,
        user_id: str,
        message_limit: int = 50,
    ) -> ChatSession:
        """
        Get the default session for a user with recent messages loaded.

        Convenience method combining get_or_create_default and get_with_messages.

        Args:
            user_id: The user's unique identifier
            message_limit: Number of recent messages to load (default: 50)

        Returns:
            Default ChatSession with messages loaded
        """
        # Ensure default session exists for this user
        default_session = await self.get_or_create_default(user_id)

        # Reload with messages
        session_with_messages = await self.get_with_messages(
            default_session.id,
            user_id=user_id,
            message_limit=message_limit,
        )

        # Should never be None since we just created/got it
        return session_with_messages or default_session

    async def update_title_from_message(
        self,
        session_id: uuid.UUID,
        first_message: str,
    ) -> ChatSession | None:
        """
        Update session title based on first message content.

        Auto-generates a title from the first user message (first 50 chars).

        Args:
            session_id: UUID of the session
            first_message: Content of the first message

        Returns:
            Updated ChatSession or None if not found
        """
        # Generate title from first message (max 50 chars)
        title = first_message[:50].strip()
        if len(first_message) > 50:
            title += "..."

        return await self.update(session_id, title=title)

    async def get_all_ordered(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ChatSession]:
        """
        Get all sessions for a user ordered by most recent activity.

        Args:
            user_id: The user's unique identifier
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of ChatSession instances ordered by updated_at desc
        """
        result = await self.session.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def create_new_session(
        self,
        user_id: str,
        title: str = "New Chat",
    ) -> ChatSession:
        """
        Create a new chat session for a user.

        Args:
            user_id: The user's unique identifier
            title: Title for the new session

        Returns:
            Created ChatSession instance
        """
        return await self.create(
            user_id=user_id,
            title=title,
            meta={},
        )

    async def count_sessions(self, user_id: str) -> int:
        """
        Count total number of sessions for a user.

        Args:
            user_id: The user's unique identifier

        Returns:
            Total session count for this user
        """
        result = await self.session.execute(
            select(func.count()).select_from(ChatSession).where(ChatSession.user_id == user_id)
        )
        return result.scalar_one()

    async def is_default_session(self, session_id: uuid.UUID) -> bool:
        """
        Check if a session is the default session.

        Args:
            session_id: UUID of the session to check

        Returns:
            True if this is the default session
        """
        session = await self.get_by_id(session_id)
        if session is None:
            return False
        return session.meta.get("is_default", False) is True

    async def belongs_to_user(self, session_id: uuid.UUID, user_id: str) -> bool:
        """
        Check if a session belongs to a specific user.

        Args:
            session_id: UUID of the session to check
            user_id: The user's unique identifier

        Returns:
            True if the session belongs to this user
        """
        session = await self.get_by_id(session_id)
        if session is None:
            return False
        return session.user_id == user_id
