"""
Repository layer for database operations.

This module provides the repository pattern implementation for data access,
separating database operations from business logic.

Repositories:
    - BaseRepository: Generic CRUD operations for any model
    - SessionRepository: ChatSession-specific operations
    - MessageRepository: Message-specific operations

Usage:
    from app.repositories import SessionRepository, MessageRepository

    async def example(db: AsyncSession):
        session_repo = SessionRepository(db)
        message_repo = MessageRepository(db)

        # Get or create default session
        default_session = await session_repo.get_or_create_default()

        # Create a message
        message = await message_repo.create_message(
            session_id=default_session.id,
            sender="user",
            content="Hello!",
        )
"""

from app.repositories.base import BaseRepository
from app.repositories.message import MessageRepository
from app.repositories.session import SessionRepository

__all__ = [
    "BaseRepository",
    "SessionRepository",
    "MessageRepository",
]
