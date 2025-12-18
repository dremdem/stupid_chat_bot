"""Repository for Message operations."""

import uuid
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.repositories.base import BaseRepository

# Valid sender types
SenderType = Literal["user", "assistant"]


class MessageRepository(BaseRepository[Message]):
    """
    Repository for Message database operations.

    Extends BaseRepository with message-specific methods.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        super().__init__(Message, session)

    async def create_message(
        self,
        session_id: uuid.UUID,
        sender: SenderType,
        content: str,
        meta: dict | None = None,
    ) -> Message:
        """
        Create a new message in a session.

        Args:
            session_id: UUID of the chat session
            sender: Who sent the message ('user' or 'assistant')
            content: Message content text
            meta: Optional metadata (e.g., AI provider info)

        Returns:
            Created Message instance
        """
        return await self.create(
            session_id=session_id,
            sender=sender,
            content=content,
            meta=meta or {},
        )

    async def get_by_session(
        self,
        session_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Message]:
        """
        Get messages for a specific session with pagination.

        Messages are ordered by creation time (oldest first).

        Args:
            session_id: UUID of the chat session
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of Message instances
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_recent(
        self,
        session_id: uuid.UUID,
        limit: int = 10,
    ) -> list[Message]:
        """
        Get the most recent messages from a session.

        Useful for providing context to AI responses.
        Returns messages in chronological order (oldest to newest).

        Args:
            session_id: UUID of the chat session
            limit: Number of recent messages to return

        Returns:
            List of Message instances (chronological order)
        """
        # Subquery to get the most recent message IDs
        # We order by created_at DESC to get recent, then reverse for chronological
        result = await self.session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())

        # Reverse to get chronological order (oldest first)
        return list(reversed(messages))

    async def count_by_session(self, session_id: uuid.UUID) -> int:
        """
        Count messages in a specific session.

        Args:
            session_id: UUID of the chat session

        Returns:
            Number of messages in the session
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count()).select_from(Message).where(Message.session_id == session_id)
        )
        return result.scalar_one()

    async def get_last_user_message(self, session_id: uuid.UUID) -> Message | None:
        """
        Get the most recent user message from a session.

        Useful for auto-generating session titles.

        Args:
            session_id: UUID of the chat session

        Returns:
            Most recent user Message or None
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .where(Message.sender == "user")
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def to_conversation_history(
        self,
        session_id: uuid.UUID,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get recent messages formatted for AI conversation context.

        Returns messages in the format expected by the AI service:
        [{"sender": "user", "content": "..."}, {"sender": "assistant", "content": "..."}]

        Args:
            session_id: UUID of the chat session
            limit: Number of recent messages to include

        Returns:
            List of message dictionaries for AI context
        """
        messages = await self.get_recent(session_id, limit)
        return [
            {
                "type": "message",
                "sender": msg.sender,
                "content": msg.content,
            }
            for msg in messages
        ]
