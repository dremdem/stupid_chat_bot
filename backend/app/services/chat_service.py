"""Chat service for managing chat sessions and message persistence."""

import logging
import uuid

from app.database import async_session_maker
from app.repositories import MessageRepository, SessionRepository

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for chat operations with database persistence.

    Handles session management and message storage for the chat application.
    Uses the repository pattern for database operations.
    """

    async def get_or_create_session(self) -> tuple[uuid.UUID, list[dict]]:
        """
        Get or create the default chat session and load history.

        Returns:
            Tuple of (session_id, conversation_history)
        """
        async with async_session_maker() as db:
            session_repo = SessionRepository(db)
            message_repo = MessageRepository(db)

            # Get or create default session
            chat_session = await session_repo.get_or_create_default()

            # Load recent conversation history
            history = await message_repo.to_conversation_history(chat_session.id, limit=50)

            await db.commit()

            logger.info(f"Session {chat_session.id}: loaded {len(history)} messages from history")

            return chat_session.id, history

    async def save_user_message(
        self,
        session_id: uuid.UUID,
        content: str,
    ) -> uuid.UUID:
        """
        Save a user message to the database.

        Args:
            session_id: The chat session ID
            content: Message content

        Returns:
            The created message ID
        """
        async with async_session_maker() as db:
            message_repo = MessageRepository(db)

            message = await message_repo.create_message(
                session_id=session_id,
                sender="user",
                content=content,
            )

            await db.commit()

            logger.debug(f"Saved user message {message.id} to session {session_id}")

            return message.id

    async def save_assistant_message(
        self,
        session_id: uuid.UUID,
        content: str,
        meta: dict | None = None,
    ) -> uuid.UUID:
        """
        Save an assistant message to the database.

        Args:
            session_id: The chat session ID
            content: Message content
            meta: Optional metadata (e.g., AI provider info)

        Returns:
            The created message ID
        """
        async with async_session_maker() as db:
            message_repo = MessageRepository(db)

            message = await message_repo.create_message(
                session_id=session_id,
                sender="assistant",
                content=content,
                meta=meta,
            )

            await db.commit()

            logger.debug(f"Saved assistant message {message.id} to session {session_id}")

            return message.id

    async def get_conversation_history(
        self,
        session_id: uuid.UUID,
        limit: int = 50,
    ) -> list[dict]:
        """
        Get conversation history for a session.

        Args:
            session_id: The chat session ID
            limit: Maximum number of messages to return

        Returns:
            List of message dictionaries with sender and content
        """
        async with async_session_maker() as db:
            message_repo = MessageRepository(db)

            history = await message_repo.to_conversation_history(session_id, limit)

            return history

    async def get_recent_context(
        self,
        session_id: uuid.UUID,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get recent messages for AI context.

        Args:
            session_id: The chat session ID
            limit: Number of recent messages for context

        Returns:
            List of message dictionaries for AI context
        """
        async with async_session_maker() as db:
            message_repo = MessageRepository(db)

            return await message_repo.to_conversation_history(session_id, limit)


# Global chat service instance
chat_service = ChatService()
