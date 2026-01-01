"""Tests for StatsRepository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.session import ChatSession
from app.models.user import User
from app.repositories.stats import StatsRepository


@pytest.mark.asyncio
async def test_get_user_counts_empty_db(async_session: AsyncSession):
    """Test user counts on empty database."""
    repo = StatsRepository(async_session)
    counts = await repo.get_user_counts()

    assert counts["registered_users"] == 0
    assert counts["unique_session_owners"] == 0
    assert counts["total_chat_sessions"] == 0


@pytest.mark.asyncio
async def test_get_user_counts_with_data(
    async_session: AsyncSession,
    sample_users: list[User],
    sample_sessions: list[ChatSession],
):
    """Test user counts with sample data."""
    repo = StatsRepository(async_session)
    counts = await repo.get_user_counts()

    assert counts["registered_users"] == 3  # admin, user1, user2
    assert counts["unique_session_owners"] == 2  # 2 anonymous sessions
    assert counts["total_chat_sessions"] == 2


@pytest.mark.asyncio
async def test_get_users_by_role(async_session: AsyncSession, sample_users: list[User]):
    """Test users grouped by role."""
    repo = StatsRepository(async_session)
    by_role = await repo.get_users_by_role()

    role_counts = {r["role"]: r["count"] for r in by_role}
    assert role_counts.get("admin") == 1
    assert role_counts.get("user") == 2


@pytest.mark.asyncio
async def test_get_top_active_users(
    async_session: AsyncSession,
    sample_users: list[User],
    sample_sessions: list[ChatSession],
    sample_messages: list[Message],
):
    """Test top active users query."""
    repo = StatsRepository(async_session)
    top_users = await repo.get_top_active_users(limit=5)

    # Should have at least one entry
    assert len(top_users) > 0

    # First user should be User One (5 messages)
    assert top_users[0]["message_count"] == 5
    assert top_users[0]["user_type"] == "registered"


@pytest.mark.asyncio
async def test_get_recent_users(async_session: AsyncSession, sample_users: list[User]):
    """Test recent users query."""
    repo = StatsRepository(async_session)
    recent = await repo.get_recent_users(limit=5)

    assert len(recent) == 3
    # Should have email/display_name
    for user in recent:
        assert user["email"] is not None or user["display_name"] is not None


@pytest.mark.asyncio
async def test_get_message_stats(
    async_session: AsyncSession,
    sample_users: list[User],
    sample_sessions: list[ChatSession],
    sample_messages: list[Message],
):
    """Test message statistics."""
    repo = StatsRepository(async_session)
    stats = await repo.get_message_stats()

    # 5 user messages from registered + 5 assistant + 3 anonymous = 13
    assert stats["total_messages"] == 13
    assert stats["user_messages"] == 8  # 5 registered + 3 anonymous
    assert stats["assistant_messages"] == 5


@pytest.mark.asyncio
async def test_get_session_stats(
    async_session: AsyncSession,
    sample_sessions: list[ChatSession],
    sample_messages: list[Message],
):
    """Test session statistics."""
    repo = StatsRepository(async_session)
    stats = await repo.get_session_stats()

    assert stats["total_sessions"] == 2
    assert stats["unique_owners"] == 2


@pytest.mark.asyncio
async def test_get_all_stats(
    async_session: AsyncSession,
    sample_users: list[User],
    sample_sessions: list[ChatSession],
    sample_messages: list[Message],
):
    """Test getting all stats at once."""
    repo = StatsRepository(async_session)
    all_stats = await repo.get_all_stats()

    # Check all sections are present
    assert "user_counts" in all_stats
    assert "users_by_role" in all_stats
    assert "top_active_users" in all_stats
    assert "recent_users" in all_stats
    assert "message_stats" in all_stats
    assert "session_stats" in all_stats
    assert all_stats["filter_days"] is None


@pytest.mark.asyncio
async def test_get_all_stats_with_days_filter(async_session: AsyncSession):
    """Test stats with days filter."""
    repo = StatsRepository(async_session)
    all_stats = await repo.get_all_stats(days=7)

    assert all_stats["filter_days"] == 7
