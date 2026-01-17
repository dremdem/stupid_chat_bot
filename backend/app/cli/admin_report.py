#!/usr/bin/env python3
"""CLI command to generate and send admin activity reports.

Usage:
    # Send report to specific email
    python -m app.cli.admin_report user@example.com

    # Send report with custom time range
    python -m app.cli.admin_report user@example.com --days 30

    # Send report to all admins
    python -m app.cli.admin_report --all-admins

    # Preview report without sending
    python -m app.cli.admin_report user@example.com --dry-run
"""

import argparse
import asyncio
import sys

from app.database import async_session_maker, close_db
from app.services.admin_report_service import AdminReportService


async def main(
    email: str | None,
    days: int,
    all_admins: bool,
    dry_run: bool,
) -> int:
    """Generate and send admin report."""
    try:
        async with async_session_maker() as db:
            service = AdminReportService(db)

            if dry_run:
                # Preview mode - just show the data
                print(f"\n{'=' * 60}")
                print("ADMIN REPORT PREVIEW (dry-run mode)")
                print(f"{'=' * 60}")

                data = await service.get_report_data(days)

                print(f"\nPeriod: {days} days")
                print(f"Total Users: {data['total_users']}")
                print(f"New Users: {data['new_users']}")
                print(f"Active Users: {data['active_users']}")
                print(f"Messages Sent: {data['total_messages']}")
                print(f"Messages Today: {data['messages_today']}")
                print(f"Blocked Users: {data['blocked_users']}")

                print("\nTop 5 Active Users:")
                for i, user in enumerate(data["top_users"], 1):
                    name = user["display_name"] or user["email"] or "Anonymous"
                    print(f"  {i}. {name} - {user['message_count']} messages")

                print("\nUsers by Role:")
                for role, count in data["users_by_role"].items():
                    print(f"  - {role}: {count}")

                if email:
                    print(f"\n[Would send to: {email}]")
                elif all_admins:
                    print("\n[Would send to: all admins]")

                print(f"\n{'=' * 60}")
                return 0

            if all_admins:
                # Send to all admins
                print(f"Sending {days}-day report to all admins...")
                result = await service.send_report_to_all_admins(days)

                if result["success"]:
                    print(f"Success: {result['message']}")
                    for admin_email, detail in result.get("details", {}).items():
                        status = "OK" if detail["success"] else "FAILED"
                        print(f"  - {admin_email}: {status}")
                    return 0
                else:
                    print(f"Error: {result['message']}")
                    return 1

            elif email:
                # Send to specific email
                print(f"Sending {days}-day report to {email}...")
                success, message = await service.generate_and_send_report(email, days)

                if success:
                    print(f"Success: {message}")
                    return 0
                else:
                    print(f"Error: {message}")
                    return 1

            else:
                print("Error: Must specify --email or --all-admins")
                return 1

    except Exception as e:
        print(f"Error: {e}")
        return 1

    finally:
        await close_db()


def run():
    """Entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Generate and send admin activity reports.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Send report to specific email
    python -m app.cli.admin_report user@example.com

    # Send 30-day report
    python -m app.cli.admin_report user@example.com --days 30

    # Send to all admins
    python -m app.cli.admin_report --all-admins

    # Preview without sending
    python -m app.cli.admin_report user@example.com --dry-run
        """,
    )

    parser.add_argument(
        "email",
        nargs="?",
        help="Recipient email address",
    )

    parser.add_argument(
        "-d",
        "--days",
        type=int,
        default=7,
        help="Number of days to include in report (default: 7)",
    )

    parser.add_argument(
        "--all-admins",
        action="store_true",
        help="Send report to all admin users",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview report data without sending email",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.email and not args.all_admins:
        parser.error("Must specify email address or --all-admins")

    exit_code = asyncio.run(
        main(
            email=args.email,
            days=args.days,
            all_admins=args.all_admins,
            dry_run=args.dry_run,
        )
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    run()
