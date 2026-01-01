"""Pytest configuration and shared fixtures."""

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.message import Message
from app.models.session import ChatSession
from app.models.user import User, UserRole


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy."""
    import asyncio

    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture
async def async_engine():
    """Create an async engine for testing with in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncSession:
    """Create an async session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def sample_users(async_session: AsyncSession) -> list[User]:
    """Create sample users for testing."""
    users = [
        User(
            id=uuid.uuid4(),
            email="admin@example.com",
            display_name="Admin User",
            role=UserRole.ADMIN.value,
            provider="email",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        User(
            id=uuid.uuid4(),
            email="user1@example.com",
            display_name="User One",
            role=UserRole.USER.value,
            provider="google",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        User(
            id=uuid.uuid4(),
            email="user2@example.com",
            display_name="User Two",
            role=UserRole.USER.value,
            provider="github",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
    ]

    for user in users:
        async_session.add(user)
    await async_session.commit()

    return users


@pytest_asyncio.fixture
async def sample_sessions(async_session: AsyncSession) -> list[ChatSession]:
    """Create sample chat sessions for testing."""
    sessions = [
        ChatSession(
            id=uuid.uuid4(),
            user_id=str(uuid.uuid4()),  # Anonymous user
            title="Anonymous Session 1",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        ChatSession(
            id=uuid.uuid4(),
            user_id=str(uuid.uuid4()),  # Another anonymous user
            title="Anonymous Session 2",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
    ]

    for session in sessions:
        async_session.add(session)
    await async_session.commit()

    return sessions


@pytest_asyncio.fixture
async def sample_messages(
    async_session: AsyncSession, sample_users: list[User], sample_sessions: list[ChatSession]
) -> list[Message]:
    """Create sample messages for testing."""
    messages = []

    # Messages from registered user
    for i in range(5):
        msg = Message(
            id=uuid.uuid4(),
            session_id=sample_sessions[0].id,
            user_id=sample_users[1].id,  # User One
            sender="user",
            content=f"User message {i}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        messages.append(msg)
        async_session.add(msg)

        # Assistant response
        assistant_msg = Message(
            id=uuid.uuid4(),
            session_id=sample_sessions[0].id,
            user_id=None,
            sender="assistant",
            content=f"Assistant response {i}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        messages.append(assistant_msg)
        async_session.add(assistant_msg)

    # Anonymous messages
    for i in range(3):
        msg = Message(
            id=uuid.uuid4(),
            session_id=sample_sessions[1].id,
            user_id=None,  # Anonymous
            sender="user",
            content=f"Anonymous message {i}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        messages.append(msg)
        async_session.add(msg)

    await async_session.commit()
    return messages
