"""Scheduler service for background tasks like periodic admin reports.

Uses APScheduler to run scheduled jobs within the FastAPI application.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import async_session_maker
from app.services.admin_report_service import AdminReportService

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


async def send_scheduled_admin_report():
    """
    Job function to send scheduled admin reports.

    This is called by the scheduler at the configured time.
    """
    logger.info("Starting scheduled admin report job")

    try:
        async with async_session_maker() as db:
            service = AdminReportService(db)

            # Determine report period based on schedule
            days = 7 if settings.admin_report_schedule == "weekly" else 1

            # Get recipients
            recipients = settings.admin_report_recipients_list

            if recipients:
                # Send to configured recipients
                for email in recipients:
                    success, message = await service.generate_and_send_report(email, days)
                    if success:
                        logger.info(f"Scheduled report sent to {email}")
                    else:
                        logger.error(f"Failed to send scheduled report to {email}: {message}")
            else:
                # Send to all admins
                result = await service.send_report_to_all_admins(days)
                if result["success"]:
                    logger.info(f"Scheduled report: {result['message']}")
                else:
                    logger.error(f"Scheduled report failed: {result['message']}")

    except Exception as e:
        logger.exception(f"Error in scheduled admin report job: {e}")


def get_cron_trigger() -> CronTrigger | None:
    """
    Build the cron trigger based on configuration.

    Returns:
        CronTrigger for the scheduled job, or None if disabled.
    """
    schedule = settings.admin_report_schedule.lower()

    if schedule == "disabled":
        return None

    # Map day names to cron day_of_week values
    day_map = {
        "mon": "mon",
        "tue": "tue",
        "wed": "wed",
        "thu": "thu",
        "fri": "fri",
        "sat": "sat",
        "sun": "sun",
        "monday": "mon",
        "tuesday": "tue",
        "wednesday": "wed",
        "thursday": "thu",
        "friday": "fri",
        "saturday": "sat",
        "sunday": "sun",
    }

    if schedule == "weekly":
        day = day_map.get(settings.admin_report_day.lower(), "mon")
        return CronTrigger(
            day_of_week=day,
            hour=settings.admin_report_hour,
            minute=settings.admin_report_minute,
            timezone="UTC",
        )
    elif schedule == "daily":
        return CronTrigger(
            hour=settings.admin_report_hour,
            minute=settings.admin_report_minute,
            timezone="UTC",
        )
    else:
        logger.warning(f"Unknown admin_report_schedule: {schedule}")
        return None


def start_scheduler():
    """
    Initialize and start the scheduler.

    Should be called during application startup.
    """
    global scheduler

    if not settings.admin_report_enabled:
        logger.info("Scheduled admin reports are disabled")
        return

    trigger = get_cron_trigger()
    if trigger is None:
        logger.info("Admin report schedule is disabled or invalid")
        return

    scheduler = AsyncIOScheduler()

    # Add the admin report job
    scheduler.add_job(
        send_scheduled_admin_report,
        trigger=trigger,
        id="admin_report",
        name="Scheduled Admin Report",
        replace_existing=True,
    )

    scheduler.start()

    # Log next run time
    job = scheduler.get_job("admin_report")
    if job and job.next_run_time:
        next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        logger.info(f"Scheduler started. Next admin report: {next_run}")
    else:
        logger.info("Scheduler started")


def stop_scheduler():
    """
    Gracefully stop the scheduler.

    Should be called during application shutdown.
    """
    global scheduler

    if scheduler is not None:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
        scheduler = None


def get_scheduler_status() -> dict:
    """
    Get current scheduler status for monitoring.

    Returns:
        Dictionary with scheduler state and job information.
    """
    if scheduler is None:
        return {
            "enabled": settings.admin_report_enabled,
            "running": False,
            "schedule": settings.admin_report_schedule,
            "next_run": None,
        }

    job = scheduler.get_job("admin_report")
    next_run = None
    if job and job.next_run_time:
        next_run = job.next_run_time.isoformat()

    return {
        "enabled": settings.admin_report_enabled,
        "running": scheduler.running,
        "schedule": settings.admin_report_schedule,
        "day": settings.admin_report_day if settings.admin_report_schedule == "weekly" else None,
        "hour": settings.admin_report_hour,
        "minute": settings.admin_report_minute,
        "recipients": settings.admin_report_recipients_list or "all admins",
        "next_run": next_run,
    }
