"""Admin report service for generating and sending activity reports."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.message import Message
from app.models.user import User, UserRole
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class AdminReportService:
    """Service for generating and sending admin activity reports."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_report_data(self, days: int = 7) -> dict:
        """
        Gather statistics for the report.

        Args:
            days: Number of days to include in the report.

        Returns:
            Dictionary with all report statistics.
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Total registered users (excluding anonymous)
        total_users_result = await self.db.execute(
            select(func.count(User.id)).where(User.role != UserRole.ANONYMOUS.value)
        )
        total_users = total_users_result.scalar() or 0

        # New users in period
        new_users_result = await self.db.execute(
            select(func.count(User.id)).where(
                and_(
                    User.role != UserRole.ANONYMOUS.value,
                    User.created_at >= cutoff,
                )
            )
        )
        new_users = new_users_result.scalar() or 0

        # Active users in period (sent at least one message)
        active_users_result = await self.db.execute(
            select(func.count(func.distinct(Message.user_id))).where(
                and_(
                    Message.user_id.isnot(None),
                    Message.sender == "user",
                    Message.created_at >= cutoff,
                )
            )
        )
        active_users = active_users_result.scalar() or 0

        # Total messages in period
        messages_result = await self.db.execute(
            select(func.count(Message.id)).where(
                and_(
                    Message.sender == "user",
                    Message.created_at >= cutoff,
                )
            )
        )
        total_messages = messages_result.scalar() or 0

        # Messages today
        messages_today_result = await self.db.execute(
            select(func.count(Message.id)).where(
                and_(
                    Message.sender == "user",
                    Message.created_at >= today_start,
                )
            )
        )
        messages_today = messages_today_result.scalar() or 0

        # Top 5 active users
        top_users_query = (
            select(
                User.email,
                User.display_name,
                func.count(Message.id).label("message_count"),
            )
            .join(Message, User.id == Message.user_id)
            .where(
                and_(
                    Message.sender == "user",
                    Message.created_at >= cutoff,
                )
            )
            .group_by(User.id)
            .order_by(func.count(Message.id).desc())
            .limit(5)
        )
        top_users_result = await self.db.execute(top_users_query)
        top_users = [
            {
                "email": row.email,
                "display_name": row.display_name,
                "message_count": row.message_count,
            }
            for row in top_users_result
        ]

        # Blocked users count
        blocked_users_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_blocked == True)  # noqa: E712
        )
        blocked_users = blocked_users_result.scalar() or 0

        # Users by role
        role_counts_result = await self.db.execute(
            select(User.role, func.count(User.id))
            .where(User.role != UserRole.ANONYMOUS.value)
            .group_by(User.role)
        )
        users_by_role = {row[0]: row[1] for row in role_counts_result}

        return {
            "period_days": days,
            "period_start": cutoff.isoformat(),
            "period_end": now.isoformat(),
            "generated_at": now.isoformat(),
            "total_users": total_users,
            "new_users": new_users,
            "active_users": active_users,
            "total_messages": total_messages,
            "messages_today": messages_today,
            "top_users": top_users,
            "blocked_users": blocked_users,
            "users_by_role": users_by_role,
        }

    def _generate_html_report(self, data: dict) -> str:
        """Generate HTML version of the report."""
        period_start = datetime.fromisoformat(data["period_start"]).strftime("%b %d, %Y")
        period_end = datetime.fromisoformat(data["period_end"]).strftime("%b %d, %Y")
        generated_at = datetime.fromisoformat(data["generated_at"]).strftime(
            "%b %d, %Y at %H:%M UTC"
        )

        # Build top users table rows
        top_users_rows = ""
        for i, user in enumerate(data["top_users"], 1):
            name = user["display_name"] or user["email"] or "Anonymous"
            msg_count = user["message_count"]
            top_users_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{i}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{name}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">
                    {msg_count}
                </td>
            </tr>
            """

        if not top_users_rows:
            top_users_rows = """
            <tr>
                <td colspan="3" style="padding: 16px; text-align: center; color: #666;">
                    No active users in this period
                </td>
            </tr>
            """

        # Build role breakdown
        role_items = ""
        for role, count in data["users_by_role"].items():
            role_display = role.replace("_", " ").title()
            role_items += f"<li>{role_display}: {count}</li>"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .header p {{
            margin: 8px 0 0 0;
            opacity: 0.9;
            font-size: 14px;
        }}
        .content {{
            padding: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8fafc;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: 700;
            color: #4f46e5;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .section {{
            margin-bottom: 24px;
        }}
        .section h2 {{
            font-size: 16px;
            color: #333;
            margin: 0 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #4f46e5;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            text-align: left;
            padding: 8px;
            background: #f8fafc;
            font-size: 12px;
            text-transform: uppercase;
            color: #666;
        }}
        th:last-child {{
            text-align: right;
        }}
        .alert {{
            background: #fef2f2;
            border-left: 4px solid #dc2626;
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 24px;
        }}
        .alert-title {{
            font-weight: 600;
            color: #dc2626;
        }}
        .footer {{
            padding: 20px 30px;
            background: #f8fafc;
            text-align: center;
            font-size: 12px;
            color: #666;
        }}
        .button {{
            display: inline-block;
            padding: 10px 20px;
            background: #4f46e5;
            color: white !important;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            margin-top: 16px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Admin Activity Report</h1>
            <p>{period_start} - {period_end} ({data['period_days']} days)</p>
        </div>

        <div class="content">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{data['total_users']}</div>
                    <div class="stat-label">Total Users</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{data['new_users']}</div>
                    <div class="stat-label">New Users</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{data['active_users']}</div>
                    <div class="stat-label">Active Users</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{data['total_messages']}</div>
                    <div class="stat-label">Messages Sent</div>
                </div>
            </div>

            {"" if data['blocked_users'] == 0 else f'''
            <div class="alert">
                <div class="alert-title">Blocked Users</div>
                <div>{data['blocked_users']} user(s) currently blocked</div>
            </div>
            '''}

            <div class="section">
                <h2>Top 5 Active Users</h2>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>User</th>
                            <th>Messages</th>
                        </tr>
                    </thead>
                    <tbody>
                        {top_users_rows}
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>Users by Role</h2>
                <ul>
                    {role_items if role_items else "<li>No registered users</li>"}
                </ul>
            </div>

            <div style="text-align: center;">
                <a href="{settings.frontend_url}/admin/stats" class="button">
                    View Full Dashboard
                </a>
            </div>
        </div>

        <div class="footer">
            <p>Stupid Chat Bot - Admin Report</p>
            <p>Generated: {generated_at}</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _generate_text_report(self, data: dict) -> str:
        """Generate plain text version of the report."""
        period_start = datetime.fromisoformat(data["period_start"]).strftime("%b %d, %Y")
        period_end = datetime.fromisoformat(data["period_end"]).strftime("%b %d, %Y")
        generated_at = datetime.fromisoformat(data["generated_at"]).strftime(
            "%b %d, %Y at %H:%M UTC"
        )

        # Build top users list
        top_users_text = ""
        for i, user in enumerate(data["top_users"], 1):
            name = user["display_name"] or user["email"] or "Anonymous"
            top_users_text += f"  {i}. {name} - {user['message_count']} messages\n"

        if not top_users_text:
            top_users_text = "  No active users in this period\n"

        # Build role breakdown
        role_text = ""
        for role, count in data["users_by_role"].items():
            role_display = role.replace("_", " ").title()
            role_text += f"  - {role_display}: {count}\n"

        blocked_alert = ""
        if data["blocked_users"] > 0:
            blocked_alert = f"""
!! ATTENTION: {data['blocked_users']} user(s) currently blocked
"""

        text = f"""
================================================================================
                         ADMIN ACTIVITY REPORT
                    {period_start} - {period_end} ({data['period_days']} days)
================================================================================

SUMMARY
-------
Total Users:    {data['total_users']}
New Users:      {data['new_users']}
Active Users:   {data['active_users']}
Messages Sent:  {data['total_messages']}
Messages Today: {data['messages_today']}
{blocked_alert}
TOP 5 ACTIVE USERS
------------------
{top_users_text}
USERS BY ROLE
-------------
{role_text if role_text else "  No registered users"}

--------------------------------------------------------------------------------
View full dashboard: {settings.frontend_url}/admin/stats
Generated: {generated_at}

Stupid Chat Bot - Admin Report
================================================================================
"""
        return text

    async def generate_and_send_report(
        self,
        to_email: str,
        days: int = 7,
    ) -> tuple[bool, str]:
        """
        Generate and send an admin report.

        Args:
            to_email: Recipient email address.
            days: Number of days to include in the report.

        Returns:
            Tuple of (success, message).
        """
        try:
            # Gather report data
            data = await self.get_report_data(days)

            # Generate report content
            html_body = self._generate_html_report(data)
            text_body = self._generate_text_report(data)

            # Build subject
            period_start = datetime.fromisoformat(data["period_start"]).strftime("%b %d")
            period_end = datetime.fromisoformat(data["period_end"]).strftime("%b %d")
            subject = f"Admin Report: {period_start} - {period_end} | Stupid Chat Bot"

            # Send email
            success = await email_service.send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )

            if success:
                logger.info(f"Admin report sent to {to_email} ({days} days)")
                return True, f"Report sent successfully to {to_email}"
            else:
                return False, "Failed to send email"

        except Exception as e:
            logger.error(f"Failed to generate/send report: {e}")
            return False, f"Error: {str(e)}"

    async def send_report_to_all_admins(self, days: int = 7) -> dict:
        """
        Send report to all admin users.

        Args:
            days: Number of days to include in the report.

        Returns:
            Dictionary with results per admin.
        """
        # Get all admin users with email
        result = await self.db.execute(
            select(User).where(
                and_(
                    User.role == UserRole.ADMIN.value,
                    User.email.isnot(None),
                    User.is_blocked == False,  # noqa: E712
                )
            )
        )
        admins = result.scalars().all()

        if not admins:
            return {"success": False, "message": "No admin users with email found"}

        results = {}
        for admin in admins:
            success, message = await self.generate_and_send_report(admin.email, days)
            results[admin.email] = {"success": success, "message": message}

        successful = sum(1 for r in results.values() if r["success"])
        return {
            "success": successful > 0,
            "message": f"Sent to {successful}/{len(admins)} admins",
            "details": results,
        }
