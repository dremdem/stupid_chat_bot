#!/usr/bin/env python
"""
CLI tool for deleting all user data by email.

Useful for development/testing to clean up test accounts.

Usage:
    # Local development
    cd backend && uv run python -m app.cli.delete_user user@example.com

    # Via invoke
    cd backend && invoke delete-user --email user@example.com

    # Via make
    make backend-delete-user EMAIL=user@example.com

    # Production (Docker)
    docker exec stupidbot-backend .venv/bin/python -m app.cli.delete_user user@example.com

    # Dry run (show what would be deleted)
    python -m app.cli.delete_user user@example.com --dry-run
"""

import argparse
import asyncio
import sys
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker, close_db
from app.models.email_verification import EmailVerificationToken
from app.models.message import Message
from app.models.session import ChatSession
from app.models.user import User
from app.models.user_session import UserSession


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Find user by email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def count_verification_tokens(db: AsyncSession, user_id: UUID) -> int:
    """Count verification tokens for a user."""
    result = await db.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.user_id == user_id)
    )
    return len(result.scalars().all())


async def count_auth_sessions(db: AsyncSession, user_id: UUID) -> int:
    """Count auth sessions for a user."""
    result = await db.execute(select(UserSession).where(UserSession.user_id == user_id))
    return len(result.scalars().all())


async def count_messages(db: AsyncSession, user_id: UUID) -> int:
    """Count messages sent by a user."""
    result = await db.execute(select(Message).where(Message.user_id == user_id))
    return len(result.scalars().all())


async def get_chat_sessions_with_user_messages(db: AsyncSession, user_id: UUID) -> list[UUID]:
    """Get chat session IDs that have messages from this user."""
    result = await db.execute(
        select(Message.session_id).where(Message.user_id == user_id).distinct()
    )
    return [row[0] for row in result.all()]


async def delete_user_data(db: AsyncSession, email: str, dry_run: bool = False) -> dict:
    """
    Delete all data associated with a user email.

    Deletes:
    - Email verification tokens (CASCADE from user)
    - Auth sessions (CASCADE from user)
    - Messages sent by the user
    - Chat sessions containing user's messages
    - User record

    Args:
        db: Database session
        email: User's email address
        dry_run: If True, only count what would be deleted

    Returns:
        Dict with counts of deleted items
    """
    # Find user
    user = await get_user_by_email(db, email)
    if not user:
        return {"error": f"User with email '{email}' not found"}

    user_id = user.id

    # Count items to be deleted
    verification_tokens_count = await count_verification_tokens(db, user_id)
    auth_sessions_count = await count_auth_sessions(db, user_id)
    messages_count = await count_messages(db, user_id)
    chat_session_ids = await get_chat_sessions_with_user_messages(db, user_id)
    chat_sessions_count = len(chat_session_ids)

    result = {
        "email": email,
        "user_id": str(user_id),
        "display_name": user.display_name,
        "provider": user.provider,
        "verification_tokens": verification_tokens_count,
        "auth_sessions": auth_sessions_count,
        "messages": messages_count,
        "chat_sessions": chat_sessions_count,
        "dry_run": dry_run,
    }

    if dry_run:
        return result

    # Delete chat sessions (cascades to messages in those sessions)
    if chat_session_ids:
        await db.execute(delete(ChatSession).where(ChatSession.id.in_(chat_session_ids)))

    # Delete any remaining messages (shouldn't be any after session deletion)
    await db.execute(delete(Message).where(Message.user_id == user_id))

    # Delete user (cascades to verification tokens and auth sessions)
    await db.delete(user)

    await db.commit()

    result["deleted"] = True
    return result


def print_result(result: dict) -> None:
    """Print deletion result in a formatted way."""
    width = 50

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print("=" * width)
    if result.get("dry_run"):
        print("    DRY RUN - No data will be deleted")
    else:
        print("         USER DATA DELETED")
    print("=" * width)

    print(f"\n User: {result['email']}")
    print(f" ID: {result['user_id']}")
    print(f" Name: {result['display_name'] or 'N/A'}")
    print(f" Provider: {result['provider']}")

    print("\n Items affected:")
    print(f"   Verification tokens: {result['verification_tokens']}")
    print(f"   Auth sessions:       {result['auth_sessions']}")
    print(f"   Messages:            {result['messages']}")
    print(f"   Chat sessions:       {result['chat_sessions']}")

    print("\n" + "=" * width)

    if result.get("dry_run"):
        print("Run without --dry-run to actually delete")
    else:
        print("All user data has been deleted!")


async def main(email: str, dry_run: bool = False) -> int:
    """
    Main entry point for the delete-user CLI.

    Args:
        email: User email to delete
        dry_run: If True, only show what would be deleted

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        async with async_session_maker() as session:
            result = await delete_user_data(session, email, dry_run)
            print_result(result)

            if "error" in result:
                return 1

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        await close_db()


def run() -> None:
    """CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Delete all data for a user by email address",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m app.cli.delete_user test@example.com
    python -m app.cli.delete_user test@example.com --dry-run
        """,
    )
    parser.add_argument(
        "email",
        type=str,
        help="Email address of the user to delete",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )

    args = parser.parse_args()
    exit_code = asyncio.run(main(args.email, args.dry_run))
    sys.exit(exit_code)


if __name__ == "__main__":
    run()
