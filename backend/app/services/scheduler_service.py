"""Scheduler service for background tasks like periodic admin reports.

Uses APScheduler to run scheduled jobs within the FastAPI application.
Schedule configuration is stored in the database and can be updated at runtime.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.database import async_session_maker
from app.models.report_schedule import ReportSchedule
from app.models.user import User
from app.services.admin_report_service import AdminReportService

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None

# Cache of current schedule for status reporting
_current_schedule: dict | None = None


async def send_scheduled_admin_report():
    """
    Job function to send scheduled admin reports.

    This is called by the scheduler at the configured time.
    Reports are sent to all users who have opted in (receive_reports=True).
    """
    logger.info("Starting scheduled admin report job")

    try:
        async with async_session_maker() as db:
            # Get schedule to determine report period
            result = await db.execute(select(ReportSchedule).where(ReportSchedule.id == 1))
            schedule = result.scalar_one_or_none()

            if not schedule or not schedule.enabled:
                logger.info("Scheduled reports are disabled, skipping")
                return

            # Determine report period based on schedule type
            days = 7 if schedule.schedule_type == "weekly" else 1

            # Get users who opted in to receive reports
            users_result = await db.execute(
                select(User).where(
                    User.receive_reports == True,  # noqa: E712
                    User.email.isnot(None),
                    User.is_blocked == False,  # noqa: E712
                )
            )
            subscribers = users_result.scalars().all()

            if not subscribers:
                logger.info("No users subscribed to reports, skipping")
                return

            service = AdminReportService(db)

            # Send to each subscriber
            success_count = 0
            for user in subscribers:
                success, message = await service.generate_and_send_report(user.email, days)
                if success:
                    success_count += 1
                    logger.info(f"Scheduled report sent to {user.email}")
                else:
                    logger.error(f"Failed to send scheduled report to {user.email}: {message}")

            logger.info(f"Scheduled report job complete: {success_count}/{len(subscribers)} sent")

    except Exception as e:
        logger.exception(f"Error in scheduled admin report job: {e}")


def _build_cron_trigger(schedule: ReportSchedule) -> CronTrigger | None:
    """
    Build the cron trigger based on schedule configuration.

    Args:
        schedule: ReportSchedule instance from database.

    Returns:
        CronTrigger for the scheduled job, or None if disabled.
    """
    if not schedule.enabled or schedule.schedule_type == "disabled":
        return None

    if schedule.schedule_type == "weekly":
        return CronTrigger(
            day_of_week=schedule.day_of_week,
            hour=schedule.hour,
            minute=schedule.minute,
            timezone="UTC",
        )
    elif schedule.schedule_type == "daily":
        return CronTrigger(
            hour=schedule.hour,
            minute=schedule.minute,
            timezone="UTC",
        )
    else:
        logger.warning(f"Unknown schedule_type: {schedule.schedule_type}")
        return None


async def _load_schedule_from_db() -> ReportSchedule | None:
    """Load schedule configuration from database."""
    try:
        async with async_session_maker() as db:
            result = await db.execute(select(ReportSchedule).where(ReportSchedule.id == 1))
            return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Failed to load schedule from database: {e}")
        return None


def _update_schedule_cache(schedule: ReportSchedule | None):
    """Update the cached schedule information."""
    global _current_schedule
    if schedule:
        _current_schedule = {
            "enabled": schedule.enabled,
            "schedule_type": schedule.schedule_type,
            "day_of_week": schedule.day_of_week,
            "hour": schedule.hour,
            "minute": schedule.minute,
        }
    else:
        _current_schedule = None


def start_scheduler():
    """
    Initialize and start the scheduler.

    Should be called during application startup.
    Loads schedule configuration from the database.
    """
    global scheduler

    import asyncio

    # Load schedule from database
    try:
        loop = asyncio.get_event_loop()
        schedule = loop.run_until_complete(_load_schedule_from_db())
    except RuntimeError:
        # No event loop running, create a new one
        schedule = asyncio.run(_load_schedule_from_db())

    if not schedule:
        logger.info("No report schedule configured in database")
        _update_schedule_cache(None)
        return

    _update_schedule_cache(schedule)

    if not schedule.enabled:
        logger.info("Scheduled admin reports are disabled")
        return

    trigger = _build_cron_trigger(schedule)
    if trigger is None:
        logger.info("Report schedule is disabled or invalid")
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


def reschedule_reports(schedule: ReportSchedule):
    """
    Reschedule the admin report job with updated settings.

    Called when schedule is updated via API.

    Args:
        schedule: Updated ReportSchedule from database.
    """
    global scheduler

    _update_schedule_cache(schedule)

    # Remove existing job if scheduler is running
    if scheduler is not None:
        try:
            scheduler.remove_job("admin_report")
        except Exception:
            pass  # Job might not exist

    if not schedule.enabled or schedule.schedule_type == "disabled":
        logger.info("Report schedule disabled")
        if scheduler is not None:
            scheduler.shutdown(wait=False)
            scheduler = None
        return

    trigger = _build_cron_trigger(schedule)
    if trigger is None:
        logger.info("Could not build trigger for schedule")
        return

    # Create scheduler if needed
    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    # Add the job with new schedule
    scheduler.add_job(
        send_scheduled_admin_report,
        trigger=trigger,
        id="admin_report",
        name="Scheduled Admin Report",
        replace_existing=True,
    )

    # Log next run time
    job = scheduler.get_job("admin_report")
    if job and job.next_run_time:
        next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        logger.info(f"Report rescheduled. Next run: {next_run}")


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
    global _current_schedule

    if _current_schedule is None:
        return {
            "enabled": False,
            "running": False,
            "schedule_type": None,
            "next_run": None,
        }

    next_run = None
    running = False

    if scheduler is not None:
        running = scheduler.running
        job = scheduler.get_job("admin_report")
        if job and job.next_run_time:
            next_run = job.next_run_time.isoformat()

    return {
        "enabled": _current_schedule.get("enabled", False),
        "running": running,
        "schedule_type": _current_schedule.get("schedule_type"),
        "day_of_week": _current_schedule.get("day_of_week"),
        "hour": _current_schedule.get("hour"),
        "minute": _current_schedule.get("minute"),
        "next_run": next_run,
    }
