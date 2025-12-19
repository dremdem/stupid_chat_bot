"""Repository for ChatSession operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.session import ChatSession
from app.repositories.base import BaseRepository

# Default session identifier - used for the single global session
DEFAULT_SESSION_TITLE = "Default Chat Session"
DEFAULT_SESSION_META = {"is_default": True}


class SessionRepository(BaseRepository[ChatSession]):
    """
    Repository for ChatSession database operations.

    Extends BaseRepository with session-specific methods.
    Following the "supersimple" approach with a single global session.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        super().__init__(ChatSession, session)

    async def get_or_create_default(self) -> ChatSession:
        """
        Get the default global session, creating it if it doesn't exist.

        This is the primary method for Phase 5's single-session approach.
        All messages go to this one shared session.

        Returns:
            The default ChatSession instance
        """
        # Try to find existing default session
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.meta["is_default"].as_boolean().is_(True))
        )
        default_session = result.scalar_one_or_none()

        if default_session is not None:
            return default_session

        # Create default session if it doesn't exist
        return await self.create(
            title=DEFAULT_SESSION_TITLE,
            meta=DEFAULT_SESSION_META,
        )

    async def get_with_messages(
        self,
        session_id: uuid.UUID,
        message_limit: int | None = None,
    ) -> ChatSession | None:
        """
        Get a session with its messages eagerly loaded.

        Args:
            session_id: UUID of the session
            message_limit: Optional limit on number of messages to load

        Returns:
            ChatSession with messages loaded, or None if not found
        """
        query = select(ChatSession).where(ChatSession.id == session_id)

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
        message_limit: int = 50,
    ) -> ChatSession:
        """
        Get the default session with recent messages loaded.

        Convenience method combining get_or_create_default and get_with_messages.

        Args:
            message_limit: Number of recent messages to load (default: 50)

        Returns:
            Default ChatSession with messages loaded
        """
        # Ensure default session exists
        default_session = await self.get_or_create_default()

        # Reload with messages
        session_with_messages = await self.get_with_messages(
            default_session.id,
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
