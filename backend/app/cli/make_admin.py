#!/usr/bin/env python
"""
CLI tool for promoting or demoting users to/from admin role.

Useful for initial admin setup and role management.

Usage:
    # Promote to admin
    cd backend && uv run python -m app.cli.make_admin user@example.com

    # Demote from admin
    cd backend && uv run python -m app.cli.make_admin user@example.com --demote

    # Via invoke
    cd backend && invoke make-admin --email user@example.com
    cd backend && invoke make-admin --email user@example.com --demote

    # Via make
    make make-admin EMAIL=user@example.com
    make make-admin EMAIL=user@example.com DEMOTE=1

    # Production (Docker)
    docker exec stupidbot-backend .venv/bin/python -m app.cli.make_admin user@example.com

    # Dry run (show what would change)
    python -m app.cli.make_admin user@example.com --dry-run
"""

import argparse
import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker, close_db
from app.models.user import User, UserRole


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Find user by email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def update_user_role(
    db: AsyncSession,
    email: str,
    demote: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    Update a user's role to admin or back to user.

    Args:
        db: Database session
        email: User's email address
        demote: If True, demote from admin to user. If False, promote to admin.
        dry_run: If True, only show what would change

    Returns:
        Dict with operation result
    """
    # Find user
    user = await get_user_by_email(db, email)
    if not user:
        return {"error": f"User with email '{email}' not found"}

    current_role = user.role
    target_role = UserRole.USER.value if demote else UserRole.ADMIN.value
    action = "demote" if demote else "promote"

    result = {
        "email": email,
        "user_id": str(user.id),
        "display_name": user.display_name,
        "provider": user.provider,
        "current_role": current_role,
        "target_role": target_role,
        "action": action,
        "dry_run": dry_run,
    }

    # Check if already in target role
    if current_role == target_role:
        result["no_change"] = True
        result["message"] = f"User is already '{target_role}'"
        return result

    # Check if trying to demote non-admin
    if demote and current_role != UserRole.ADMIN.value:
        result["no_change"] = True
        result["message"] = f"User is not an admin (current role: '{current_role}')"
        return result

    if dry_run:
        result["would_change"] = True
        return result

    # Update role
    user.role = target_role
    await db.commit()
    await db.refresh(user)

    result["updated"] = True
    return result


def print_result(result: dict) -> None:
    """Print operation result in a formatted way."""
    width = 50

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print("=" * width)
    if result.get("dry_run"):
        print("    DRY RUN - No changes will be made")
    elif result.get("no_change"):
        print("         NO CHANGE NEEDED")
    else:
        print("         USER ROLE UPDATED")
    print("=" * width)

    print(f"\n User: {result['email']}")
    print(f" ID: {result['user_id']}")
    print(f" Name: {result['display_name'] or 'N/A'}")
    print(f" Provider: {result['provider']}")

    if result.get("no_change"):
        print(f"\n {result['message']}")
    else:
        arrow = "→"
        print(f"\n Role change: {result['current_role']} {arrow} {result['target_role']}")

    print("\n" + "=" * width)

    if result.get("dry_run"):
        print("Run without --dry-run to apply changes")
    elif result.get("no_change"):
        print("No action taken")
    elif result.get("updated"):
        if result["action"] == "promote":
            print("User is now an admin!")
        else:
            print("User has been demoted to regular user")


async def main(email: str, demote: bool = False, dry_run: bool = False) -> int:
    """
    Main entry point for the make-admin CLI.

    Args:
        email: User email to update
        demote: If True, demote from admin
        dry_run: If True, only show what would change

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        async with async_session_maker() as session:
            result = await update_user_role(session, email, demote, dry_run)
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
        description="Promote or demote a user to/from admin role",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m app.cli.make_admin admin@example.com
    python -m app.cli.make_admin admin@example.com --demote
    python -m app.cli.make_admin admin@example.com --dry-run
        """,
    )
    parser.add_argument(
        "email",
        type=str,
        help="Email address of the user to promote/demote",
    )
    parser.add_argument(
        "-d",
        "--demote",
        action="store_true",
        help="Demote user from admin to regular user",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would change without actually modifying",
    )

    args = parser.parse_args()
    exit_code = asyncio.run(main(args.email, args.demote, args.dry_run))
    sys.exit(exit_code)


if __name__ == "__main__":
    run()
