"""Repository for database statistics queries."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.session import ChatSession
from app.models.user import User


class StatsRepository:
    """
    Repository for gathering database statistics.

    Provides methods to query aggregate statistics about users,
    sessions, and messages without inheriting from BaseRepository
    since it doesn't operate on a single model.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def get_user_counts(self, days: int | None = None) -> dict:
        """
        Get counts of registered users vs anonymous session owners.

        Args:
            days: If provided, only count users/sessions created within last N days

        Returns:
            Dictionary with user count statistics
        """
        date_filter = None
        if days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            date_filter = cutoff

        # Count registered users
        user_query = select(func.count()).select_from(User)
        if date_filter:
            user_query = user_query.where(User.created_at >= date_filter)
        result = await self.session.execute(user_query)
        registered_users = result.scalar_one()

        # Count unique session owners (user_id strings from cookies)
        session_query = select(func.count(func.distinct(ChatSession.user_id)))
        if date_filter:
            session_query = session_query.where(ChatSession.created_at >= date_filter)
        result = await self.session.execute(session_query)
        unique_session_owners = result.scalar_one()

        # Count total chat sessions
        total_sessions_query = select(func.count()).select_from(ChatSession)
        if date_filter:
            total_sessions_query = total_sessions_query.where(ChatSession.created_at >= date_filter)
        result = await self.session.execute(total_sessions_query)
        total_sessions = result.scalar_one()

        return {
            "registered_users": registered_users,
            "unique_session_owners": unique_session_owners,
            "total_chat_sessions": total_sessions,
        }

    async def get_users_by_role(self, days: int | None = None) -> list[dict]:
        """
        Get count of users grouped by role.

        Args:
            days: If provided, only count users created within last N days

        Returns:
            List of dicts with role and count
        """
        query = select(User.role, func.count(User.id).label("count")).group_by(User.role)

        if days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            query = query.where(User.created_at >= cutoff)

        query = query.order_by(func.count(User.id).desc())
        result = await self.session.execute(query)

        return [{"role": row.role, "count": row.count} for row in result.all()]

    async def get_top_active_users(self, limit: int = 5, days: int | None = None) -> list[dict]:
        """
        Get users with most messages sent.

        Includes both registered users (by user_id FK in messages)
        and anonymous session owners (by session's user_id).

        Args:
            limit: Number of top users to return
            days: If provided, only count messages from last N days

        Returns:
            List of dicts with user info and message count
        """
        # For registered users: count messages where user_id is set
        registered_query = (
            select(
                User.id,
                User.email,
                User.display_name,
                func.count(Message.id).label("message_count"),
                text("'registered' as user_type"),
            )
            .join(Message, Message.user_id == User.id)
            .where(Message.sender == "user")
            .group_by(User.id)
        )

        if days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            registered_query = registered_query.where(Message.created_at >= cutoff)

        result = await self.session.execute(
            registered_query.order_by(func.count(Message.id).desc()).limit(limit)
        )
        registered_users = result.all()

        # For anonymous: count user messages by session owner
        # (messages where user_id is NULL, grouped by session's user_id)
        anonymous_query = (
            select(
                ChatSession.user_id.label("session_owner"),
                func.count(Message.id).label("message_count"),
            )
            .join(Message, Message.session_id == ChatSession.id)
            .where(Message.sender == "user")
            .where(Message.user_id.is_(None))
            .group_by(ChatSession.user_id)
        )

        if days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            anonymous_query = anonymous_query.where(Message.created_at >= cutoff)

        result = await self.session.execute(
            anonymous_query.order_by(func.count(Message.id).desc()).limit(limit)
        )
        anonymous_sessions = result.all()

        # Combine and sort
        combined = []

        for row in registered_users:
            combined.append(
                {
                    "identifier": row.email or row.display_name or str(row.id)[:8],
                    "display_name": row.display_name,
                    "message_count": row.message_count,
                    "user_type": "registered",
                }
            )

        for row in anonymous_sessions:
            combined.append(
                {
                    "identifier": f"Anonymous ({row.session_owner[:8]}...)",
                    "display_name": None,
                    "message_count": row.message_count,
                    "user_type": "anonymous",
                }
            )

        # Sort by message count and take top N
        combined.sort(key=lambda x: x["message_count"], reverse=True)
        return combined[:limit]

    async def get_recent_users(self, limit: int = 5, days: int | None = None) -> list[dict]:
        """
        Get most recently registered users.

        Args:
            limit: Number of users to return
            days: If provided, only include users from last N days

        Returns:
            List of dicts with user info and registration date
        """
        query = select(
            User.id,
            User.email,
            User.display_name,
            User.role,
            User.provider,
            User.created_at,
        ).order_by(User.created_at.desc())

        if days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            query = query.where(User.created_at >= cutoff)

        result = await self.session.execute(query.limit(limit))

        return [
            {
                "id": str(row.id),
                "email": row.email,
                "display_name": row.display_name,
                "role": row.role,
                "provider": row.provider,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in result.all()
        ]

    async def get_message_stats(self, days: int | None = None) -> dict:
        """
        Get message statistics.

        Args:
            days: If provided, only include messages from last N days

        Returns:
            Dictionary with message statistics
        """
        date_filter = None
        if days is not None:
            date_filter = datetime.now(timezone.utc) - timedelta(days=days)

        # Total messages
        total_query = select(func.count()).select_from(Message)
        if date_filter:
            total_query = total_query.where(Message.created_at >= date_filter)
        result = await self.session.execute(total_query)
        total_messages = result.scalar_one()

        # Messages by sender type
        by_sender_query = select(Message.sender, func.count(Message.id).label("count")).group_by(
            Message.sender
        )
        if date_filter:
            by_sender_query = by_sender_query.where(Message.created_at >= date_filter)
        result = await self.session.execute(by_sender_query)
        by_sender = {row.sender: row.count for row in result.all()}

        # Messages today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count()).select_from(Message).where(Message.created_at >= today_start)
        )
        messages_today = result.scalar_one()

        # Average messages per session (for sessions with messages)
        avg_query = text(
            """
            SELECT AVG(msg_count) as avg_per_session
            FROM (
                SELECT session_id, COUNT(*) as msg_count
                FROM messages
                GROUP BY session_id
            )
            """
        )
        result = await self.session.execute(avg_query)
        row = result.fetchone()
        avg_per_session = round(row[0], 1) if row and row[0] else 0

        return {
            "total_messages": total_messages,
            "user_messages": by_sender.get("user", 0),
            "assistant_messages": by_sender.get("assistant", 0),
            "messages_today": messages_today,
            "avg_per_session": avg_per_session,
        }

    async def get_session_stats(self, days: int | None = None) -> dict:
        """
        Get chat session statistics.

        Args:
            days: If provided, only include sessions from last N days

        Returns:
            Dictionary with session statistics
        """
        date_filter = None
        if days is not None:
            date_filter = datetime.now(timezone.utc) - timedelta(days=days)

        # Total sessions
        total_query = select(func.count()).select_from(ChatSession)
        if date_filter:
            total_query = total_query.where(ChatSession.created_at >= date_filter)
        result = await self.session.execute(total_query)
        total_sessions = result.scalar_one()

        # Sessions active today (have messages today)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count(func.distinct(Message.session_id))).where(
                Message.created_at >= today_start
            )
        )
        active_today = result.scalar_one()

        # Unique session owners
        owners_query = select(func.count(func.distinct(ChatSession.user_id)))
        if date_filter:
            owners_query = owners_query.where(ChatSession.created_at >= date_filter)
        result = await self.session.execute(owners_query)
        unique_owners = result.scalar_one()

        return {
            "total_sessions": total_sessions,
            "active_today": active_today,
            "unique_owners": unique_owners,
        }

    async def get_all_stats(self, days: int | None = None) -> dict:
        """
        Get all statistics in a single call.

        Args:
            days: If provided, limit all stats to last N days

        Returns:
            Dictionary with all statistics grouped by category
        """
        return {
            "user_counts": await self.get_user_counts(days),
            "users_by_role": await self.get_users_by_role(days),
            "top_active_users": await self.get_top_active_users(5, days),
            "recent_users": await self.get_recent_users(5, days),
            "message_stats": await self.get_message_stats(days),
            "session_stats": await self.get_session_stats(days),
            "filter_days": days,
        }
