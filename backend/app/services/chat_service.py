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

    # --- Session Management Methods (Phase 5.4) ---

    async def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """
        List all chat sessions.

        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            Tuple of (list of session dicts, total count)
        """
        async with async_session_maker() as db:
            session_repo = SessionRepository(db)

            sessions = await session_repo.get_all_ordered(limit=limit, offset=offset)
            total = await session_repo.count_sessions()

            return [s.to_dict() for s in sessions], total

    async def create_new_session(self, title: str = "New Chat") -> dict:
        """
        Create a new chat session.

        Args:
            title: Title for the new session

        Returns:
            Created session as dictionary
        """
        async with async_session_maker() as db:
            session_repo = SessionRepository(db)

            session = await session_repo.create_new_session(title=title)
            await db.commit()

            logger.info(f"Created new session: {session.id} - {title}")

            return session.to_dict()

    async def get_session(self, session_id: uuid.UUID) -> dict | None:
        """
        Get a specific session by ID.

        Args:
            session_id: The session UUID

        Returns:
            Session as dictionary or None if not found
        """
        async with async_session_maker() as db:
            session_repo = SessionRepository(db)

            session = await session_repo.get_by_id(session_id)

            if session is None:
                return None

            return session.to_dict()

    async def get_session_with_history(
        self,
        session_id: uuid.UUID,
    ) -> tuple[uuid.UUID, list[dict]] | None:
        """
        Get a session with its conversation history.

        Args:
            session_id: The session UUID

        Returns:
            Tuple of (session_id, history) or None if not found
        """
        async with async_session_maker() as db:
            session_repo = SessionRepository(db)
            message_repo = MessageRepository(db)

            session = await session_repo.get_by_id(session_id)

            if session is None:
                return None

            history = await message_repo.to_conversation_history(session_id, limit=50)

            logger.info(f"Session {session_id}: loaded {len(history)} messages")

            return session_id, history

    async def update_session_title(
        self,
        session_id: uuid.UUID,
        title: str,
    ) -> dict | None:
        """
        Update a session's title.

        Args:
            session_id: The session UUID
            title: New title

        Returns:
            Updated session as dictionary or None if not found
        """
        async with async_session_maker() as db:
            session_repo = SessionRepository(db)

            session = await session_repo.update(session_id, title=title)
            await db.commit()

            if session is None:
                return None

            logger.info(f"Updated session {session_id} title to: {title}")

            return session.to_dict()

    async def delete_session(self, session_id: uuid.UUID) -> bool:
        """
        Delete a session and all its messages.

        Note: Cannot delete the default session.

        Args:
            session_id: The session UUID

        Returns:
            True if deleted, False if not found or is default session
        """
        async with async_session_maker() as db:
            session_repo = SessionRepository(db)

            # Check if this is the default session
            if await session_repo.is_default_session(session_id):
                logger.warning(f"Attempted to delete default session {session_id}")
                return False

            deleted = await session_repo.delete(session_id)
            await db.commit()

            if deleted:
                logger.info(f"Deleted session {session_id}")

            return deleted


# Global chat service instance
chat_service = ChatService()
