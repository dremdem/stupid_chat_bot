#!/usr/bin/env python
"""
CLI tool for displaying database statistics.

Usage:
    # Local development
    cd backend && uv run python -m app.cli.stats

    # Via invoke
    cd backend && invoke db-stats

    # Via make
    make backend-db-stats

    # Production (Docker)
    docker exec stupidbot-backend .venv/bin/python -m app.cli.stats

    # With time filter
    python -m app.cli.stats --days 7
"""

import argparse
import asyncio
import sys
from datetime import datetime

from app.database import async_session_maker, close_db
from app.repositories.stats import StatsRepository


def format_datetime(iso_string: str | None) -> str:
    """Format ISO datetime string for display."""
    if not iso_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return iso_string[:16] if iso_string else "N/A"


def print_stats(stats: dict) -> None:
    """Print statistics in a formatted way."""
    width = 60

    # Header
    print("=" * width)
    if stats.get("filter_days"):
        print(f"       DATABASE STATISTICS (Last {stats['filter_days']} days)")
    else:
        print("              DATABASE STATISTICS")
    print("=" * width)

    # User counts
    uc = stats["user_counts"]
    print("\n USER COUNTS")
    print(f"   Registered users:     {uc['registered_users']}")
    print(f"   Unique session owners:{uc['unique_session_owners']}")
    print(f"   Total chat sessions:  {uc['total_chat_sessions']}")

    # Users by role
    roles = stats["users_by_role"]
    if roles:
        print("\n USERS BY ROLE")
        for r in roles:
            print(f"   {r['role']:<15} {r['count']}")
    else:
        print("\n USERS BY ROLE")
        print("   No registered users")

    # Top active users
    top_users = stats["top_active_users"]
    print("\n TOP 5 ACTIVE USERS (by messages)")
    if top_users:
        for i, u in enumerate(top_users, 1):
            identifier = u["identifier"][:30]
            msg_count = u["message_count"]
            user_type = u["user_type"]
            type_marker = "" if user_type == "registered" else " [anon]"
            print(f"   {i}. {identifier:<30} {msg_count:>5} msgs{type_marker}")
    else:
        print("   No messages found")

    # Recent users
    recent = stats["recent_users"]
    print("\n LAST 5 REGISTERED USERS")
    if recent:
        for i, u in enumerate(recent, 1):
            identifier = u["email"] or u["display_name"] or u["id"][:8]
            identifier = identifier[:30]
            date = format_datetime(u["created_at"])
            print(f"   {i}. {identifier:<30} {date}")
    else:
        print("   No registered users")

    # Message stats
    ms = stats["message_stats"]
    print("\n MESSAGE STATISTICS")
    print(f"   Total messages:       {ms['total_messages']}")
    print(f"   User messages:        {ms['user_messages']}")
    print(f"   Assistant messages:   {ms['assistant_messages']}")
    print(f"   Messages today:       {ms['messages_today']}")
    print(f"   Avg per session:      {ms['avg_per_session']}")

    # Session stats
    ss = stats["session_stats"]
    print("\n SESSION STATISTICS")
    print(f"   Total sessions:       {ss['total_sessions']}")
    print(f"   Active today:         {ss['active_today']}")
    print(f"   Unique owners:        {ss['unique_owners']}")

    print("\n" + "=" * width)


async def main(days: int | None = None) -> int:
    """
    Main entry point for the stats CLI.

    Args:
        days: If provided, limit stats to last N days

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        async with async_session_maker() as session:
            repo = StatsRepository(session)
            stats = await repo.get_all_stats(days)
            print_stats(stats)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        # Properly close the database engine to avoid hanging
        await close_db()


def run() -> None:
    """CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Display database statistics for Stupid Chat Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m app.cli.stats           # All-time statistics
    python -m app.cli.stats --days 7  # Last 7 days only
    python -m app.cli.stats -d 30     # Last 30 days
        """,
    )
    parser.add_argument(
        "-d",
        "--days",
        type=int,
        default=None,
        help="Limit statistics to last N days (default: unlimited)",
    )

    args = parser.parse_args()
    exit_code = asyncio.run(main(args.days))
    sys.exit(exit_code)


if __name__ == "__main__":
    run()
