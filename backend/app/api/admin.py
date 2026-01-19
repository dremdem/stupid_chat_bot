"""Admin API endpoints for user management and statistics."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Date

from app.database import get_db
from app.dependencies import require_admin
from app.models.message import Message
from app.models.report_schedule import ReportSchedule
from app.models.user import User, UserRole
from app.services.admin_report_service import AdminReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ============================================================================
# Pydantic Models
# ============================================================================


class UserListItem(BaseModel):
    """User item in list response."""

    id: str
    email: str | None
    display_name: str | None
    role: str
    provider: str
    is_blocked: bool
    is_email_verified: bool
    message_limit: int | None
    message_count: int
    created_at: str
    updated_at: str


class UserListResponse(BaseModel):
    """Response for user list endpoint."""

    users: list[UserListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserDetailResponse(BaseModel):
    """Response for user detail endpoint."""

    id: str
    email: str | None
    display_name: str | None
    avatar_url: str | None
    role: str
    provider: str
    is_blocked: bool
    is_email_verified: bool
    message_limit: int | None
    context_window_size: int
    message_count: int
    created_at: str
    updated_at: str


class UpdateRoleRequest(BaseModel):
    """Request to update user role."""

    role: str = Field(..., pattern="^(user|unlimited|admin)$")


class UpdateBlockRequest(BaseModel):
    """Request to block/unblock user."""

    is_blocked: bool


class UpdateLimitRequest(BaseModel):
    """Request to update message limit."""

    message_limit: int | None = Field(None, ge=0, le=10000)


class AdminActionResponse(BaseModel):
    """Response for admin actions."""

    success: bool
    message: str
    user: UserDetailResponse | None = None


# ============================================================================
# Statistics Pydantic Models
# ============================================================================


class StatsSummaryResponse(BaseModel):
    """Response for statistics summary."""

    total_users: int
    active_users_7d: int
    total_messages: int
    messages_today: int
    messages_7d: int
    new_users_today: int
    new_users_7d: int


class DailyActivityItem(BaseModel):
    """Single day activity data."""

    date: str
    messages: int
    new_users: int


class DailyActivityResponse(BaseModel):
    """Response for daily activity data."""

    days: int
    data: list[DailyActivityItem]


class TopUserItem(BaseModel):
    """Top user item."""

    id: str
    email: str | None
    display_name: str | None
    role: str
    message_count: int
    last_message_at: str | None
    created_at: str


class TopUsersResponse(BaseModel):
    """Response for top users."""

    users: list[TopUserItem]
    total: int
    days: int


class MessageItem(BaseModel):
    """Message item for user messages list."""

    id: str
    sender: str
    content: str
    created_at: str
    session_id: str


class UserMessagesResponse(BaseModel):
    """Response for user messages."""

    user_id: str
    user_email: str | None
    user_display_name: str | None
    messages: list[MessageItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Helper Functions
# ============================================================================


async def get_user_message_count(db: AsyncSession, user_id: UUID) -> int:
    """Get total message count for a user."""
    result = await db.execute(
        select(func.count(Message.id)).where(
            Message.user_id == user_id,
            Message.sender == "user",
        )
    )
    return result.scalar() or 0


async def user_to_detail_response(user: User, message_count: int) -> UserDetailResponse:
    """Convert user to detail response."""
    return UserDetailResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        role=user.role,
        provider=user.provider,
        is_blocked=user.is_blocked,
        is_email_verified=user.is_email_verified,
        message_limit=user.message_limit,
        context_window_size=user.context_window_size,
        message_count=message_count,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/users", response_model=UserListResponse)
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=100)] = None,
    role: Annotated[str | None, Query(pattern="^(user|unlimited|admin)$")] = None,
    blocked: Annotated[bool | None, Query()] = None,
):
    """
    List all users with pagination and filtering.

    Admin only endpoint.
    """
    # Build base query
    query = select(User)

    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_pattern)) | (User.display_name.ilike(search_pattern))
        )

    if role:
        query = query.where(User.role == role)

    if blocked is not None:
        query = query.where(User.is_blocked == blocked)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()

    # Get message counts for each user
    user_items = []
    for user in users:
        message_count = await get_user_message_count(db, user.id)
        user_items.append(
            UserListItem(
                id=str(user.id),
                email=user.email,
                display_name=user.display_name,
                role=user.role,
                provider=user.provider,
                is_blocked=user.is_blocked,
                is_email_verified=user.is_email_verified,
                message_limit=user.message_limit,
                message_count=message_count,
                created_at=user.created_at.isoformat(),
                updated_at=user.updated_at.isoformat(),
            )
        )

    total_pages = (total + page_size - 1) // page_size

    return UserListResponse(
        users=user_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific user.

    Admin only endpoint.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    message_count = await get_user_message_count(db, user.id)
    return await user_to_detail_response(user, message_count)


@router.patch("/users/{user_id}/role", response_model=AdminActionResponse)
async def update_user_role(
    user_id: UUID,
    data: UpdateRoleRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a user's role.

    Admin only endpoint.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from demoting themselves
    if user.id == admin.id and data.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )

    old_role = user.role
    user.role = data.role
    await db.commit()
    await db.refresh(user)

    message_count = await get_user_message_count(db, user.id)
    logger.info(
        f"Admin {admin.email} changed role for user {user.email}: {old_role} -> {data.role}"
    )

    return AdminActionResponse(
        success=True,
        message=f"Role updated from '{old_role}' to '{data.role}'",
        user=await user_to_detail_response(user, message_count),
    )


@router.patch("/users/{user_id}/block", response_model=AdminActionResponse)
async def update_user_block_status(
    user_id: UUID,
    data: UpdateBlockRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Block or unblock a user.

    Admin only endpoint.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from blocking themselves
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot block yourself",
        )

    user.is_blocked = data.is_blocked
    await db.commit()
    await db.refresh(user)

    message_count = await get_user_message_count(db, user.id)
    action = "blocked" if data.is_blocked else "unblocked"
    logger.info(f"Admin {admin.email} {action} user {user.email}")

    return AdminActionResponse(
        success=True,
        message=f"User {action} successfully",
        user=await user_to_detail_response(user, message_count),
    )


@router.patch("/users/{user_id}/limit", response_model=AdminActionResponse)
async def update_user_message_limit(
    user_id: UUID,
    data: UpdateLimitRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a user's message limit.

    Set to null to use default limit for their role.

    Admin only endpoint.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    old_limit = user.message_limit
    user.message_limit = data.message_limit
    await db.commit()
    await db.refresh(user)

    message_count = await get_user_message_count(db, user.id)
    limit_str = str(data.message_limit) if data.message_limit is not None else "default"
    old_limit_str = str(old_limit) if old_limit is not None else "default"
    logger.info(
        f"Admin {admin.email} changed message limit for user {user.email}: "
        f"{old_limit_str} -> {limit_str}"
    )

    return AdminActionResponse(
        success=True,
        message=f"Message limit updated to {limit_str}",
        user=await user_to_detail_response(user, message_count),
    )


# ============================================================================
# Statistics Endpoints
# ============================================================================


@router.get("/stats/summary", response_model=StatsSummaryResponse)
async def get_stats_summary(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get summary statistics for the admin dashboard.

    Returns total users, active users, message counts, etc.
    Admin only endpoint.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = now - timedelta(days=7)

    # Total users (excluding anonymous role)
    total_users_result = await db.execute(
        select(func.count(User.id)).where(User.role != UserRole.ANONYMOUS.value)
    )
    total_users = total_users_result.scalar() or 0

    # Active users in last 7 days (users who sent messages)
    active_users_result = await db.execute(
        select(func.count(func.distinct(Message.user_id))).where(
            and_(
                Message.user_id.isnot(None),
                Message.sender == "user",
                Message.created_at >= seven_days_ago,
            )
        )
    )
    active_users_7d = active_users_result.scalar() or 0

    # Total messages (user messages only)
    total_messages_result = await db.execute(
        select(func.count(Message.id)).where(Message.sender == "user")
    )
    total_messages = total_messages_result.scalar() or 0

    # Messages today
    messages_today_result = await db.execute(
        select(func.count(Message.id)).where(
            and_(
                Message.sender == "user",
                Message.created_at >= today_start,
            )
        )
    )
    messages_today = messages_today_result.scalar() or 0

    # Messages in last 7 days
    messages_7d_result = await db.execute(
        select(func.count(Message.id)).where(
            and_(
                Message.sender == "user",
                Message.created_at >= seven_days_ago,
            )
        )
    )
    messages_7d = messages_7d_result.scalar() or 0

    # New users today
    new_users_today_result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.role != UserRole.ANONYMOUS.value,
                User.created_at >= today_start,
            )
        )
    )
    new_users_today = new_users_today_result.scalar() or 0

    # New users in last 7 days
    new_users_7d_result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.role != UserRole.ANONYMOUS.value,
                User.created_at >= seven_days_ago,
            )
        )
    )
    new_users_7d = new_users_7d_result.scalar() or 0

    return StatsSummaryResponse(
        total_users=total_users,
        active_users_7d=active_users_7d,
        total_messages=total_messages,
        messages_today=messages_today,
        messages_7d=messages_7d,
        new_users_today=new_users_today,
        new_users_7d=new_users_7d,
    )


@router.get("/stats/daily-activity", response_model=DailyActivityResponse)
async def get_daily_activity(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    days: Annotated[int, Query(ge=7, le=90)] = 30,
):
    """
    Get daily activity data for charts.

    Returns message counts and new user registrations per day.
    Admin only endpoint.
    """
    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(days=days)).date()

    # Get daily message counts
    messages_query = (
        select(
            cast(Message.created_at, Date).label("date"),
            func.count(Message.id).label("count"),
        )
        .where(
            and_(
                Message.sender == "user",
                cast(Message.created_at, Date) >= start_date,
            )
        )
        .group_by(cast(Message.created_at, Date))
    )
    messages_result = await db.execute(messages_query)
    messages_by_date = {row.date: row.count for row in messages_result}

    # Get daily new user counts
    users_query = (
        select(
            cast(User.created_at, Date).label("date"),
            func.count(User.id).label("count"),
        )
        .where(
            and_(
                User.role != UserRole.ANONYMOUS.value,
                cast(User.created_at, Date) >= start_date,
            )
        )
        .group_by(cast(User.created_at, Date))
    )
    users_result = await db.execute(users_query)
    users_by_date = {row.date: row.count for row in users_result}

    # Build response with all days (including zeros)
    data = []
    current_date = start_date
    end_date = now.date()
    while current_date <= end_date:
        data.append(
            DailyActivityItem(
                date=current_date.isoformat(),
                messages=messages_by_date.get(current_date, 0),
                new_users=users_by_date.get(current_date, 0),
            )
        )
        current_date += timedelta(days=1)

    return DailyActivityResponse(days=days, data=data)


@router.get("/stats/top-users", response_model=TopUsersResponse)
async def get_top_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
):
    """
    Get top active users by message count.

    Admin only endpoint.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Subquery for message counts and last message time
    message_stats = (
        select(
            Message.user_id,
            func.count(Message.id).label("message_count"),
            func.max(Message.created_at).label("last_message_at"),
        )
        .where(
            and_(
                Message.user_id.isnot(None),
                Message.sender == "user",
                Message.created_at >= cutoff_date,
            )
        )
        .group_by(Message.user_id)
        .subquery()
    )

    # Join with users and order by message count
    query = (
        select(
            User,
            message_stats.c.message_count,
            message_stats.c.last_message_at,
        )
        .join(message_stats, User.id == message_stats.c.user_id)
        .order_by(message_stats.c.message_count.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    users = [
        TopUserItem(
            id=str(row.User.id),
            email=row.User.email,
            display_name=row.User.display_name,
            role=row.User.role,
            message_count=row.message_count,
            last_message_at=row.last_message_at.isoformat() if row.last_message_at else None,
            created_at=row.User.created_at.isoformat(),
        )
        for row in rows
    ]

    return TopUsersResponse(users=users, total=len(users), days=days)


@router.get("/stats/user-messages/{user_id}", response_model=UserMessagesResponse)
async def get_user_messages(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """
    Get message history for a specific user (read-only).

    Admin only endpoint for reviewing user conversations.
    """
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get total message count
    count_result = await db.execute(
        select(func.count(Message.id)).where(Message.user_id == user_id)
    )
    total = count_result.scalar() or 0

    # Get paginated messages
    offset = (page - 1) * page_size
    messages_result = await db.execute(
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    messages = messages_result.scalars().all()

    message_items = [
        MessageItem(
            id=str(msg.id),
            sender=msg.sender,
            content=msg.content,
            created_at=msg.created_at.isoformat(),
            session_id=str(msg.session_id),
        )
        for msg in messages
    ]

    total_pages = (total + page_size - 1) // page_size

    return UserMessagesResponse(
        user_id=str(user.id),
        user_email=user.email,
        user_display_name=user.display_name,
        messages=message_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ============================================================================
# Report Pydantic Models
# ============================================================================


class SendReportRequest(BaseModel):
    """Request to send admin report."""

    email: str | None = Field(None, description="Recipient email (required if not all_admins)")
    days: int = Field(default=7, ge=1, le=365, description="Days to include in report")
    all_admins: bool = Field(default=False, description="Send to all admin users")


class SendReportResponse(BaseModel):
    """Response for send report endpoint."""

    success: bool
    message: str
    details: dict | None = None


# ============================================================================
# Report Endpoints
# ============================================================================


@router.post("/reports/send", response_model=SendReportResponse)
async def send_admin_report(
    data: SendReportRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Send admin activity report via email.

    Can send to a specific email or all admin users.
    Admin only endpoint.
    """
    service = AdminReportService(db)

    if data.all_admins:
        result = await service.send_report_to_all_admins(data.days)
        logger.info(f"Admin {admin.email} sent report to all admins ({data.days} days)")
        return SendReportResponse(
            success=result["success"],
            message=result["message"],
            details=result.get("details"),
        )

    if not data.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify email or set all_admins=true",
        )

    success, message = await service.generate_and_send_report(data.email, data.days)
    logger.info(f"Admin {admin.email} sent report to {data.email} ({data.days} days)")

    return SendReportResponse(
        success=success,
        message=message,
    )


# ============================================================================
# Scheduler Status Endpoint
# ============================================================================


@router.get("/scheduler/status")
async def get_scheduler_status_endpoint(
    admin: User = Depends(require_admin),
):
    """
    Get the status of the scheduled reports scheduler.

    Returns information about whether scheduled reports are enabled,
    the schedule configuration, and the next scheduled run time.

    Admin only endpoint.
    """
    from app.services.scheduler_service import get_scheduler_status

    return get_scheduler_status()


# ============================================================================
# Report Schedule Management (Database-backed)
# ============================================================================


class ReportScheduleResponse(BaseModel):
    """Response for report schedule."""

    enabled: bool
    schedule_type: str
    day_of_week: str
    hour: int
    minute: int
    updated_at: str | None
    next_run: str | None = None
    subscribed_users_count: int = 0


class UpdateScheduleRequest(BaseModel):
    """Request to update report schedule."""

    enabled: bool | None = None
    schedule_type: str | None = Field(None, pattern="^(weekly|daily|disabled)$")
    day_of_week: str | None = Field(None, pattern="^(mon|tue|wed|thu|fri|sat|sun)$")
    hour: int | None = Field(None, ge=0, le=23)
    minute: int | None = Field(None, ge=0, le=59)


@router.get("/reports/schedule", response_model=ReportScheduleResponse)
async def get_report_schedule(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current report schedule configuration.

    Admin only endpoint.
    """
    from app.services.scheduler_service import get_scheduler_status

    # Get or create schedule record
    result = await db.execute(select(ReportSchedule).where(ReportSchedule.id == 1))
    schedule = result.scalar_one_or_none()

    if not schedule:
        # Create default schedule
        schedule = ReportSchedule(id=1)
        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)

    # Count users subscribed to reports
    count_result = await db.execute(
        select(func.count(User.id)).where(User.receive_reports == True)  # noqa: E712
    )
    subscribed_count = count_result.scalar() or 0

    # Get next run time from scheduler
    scheduler_status = get_scheduler_status()

    return ReportScheduleResponse(
        enabled=schedule.enabled,
        schedule_type=schedule.schedule_type,
        day_of_week=schedule.day_of_week,
        hour=schedule.hour,
        minute=schedule.minute,
        updated_at=schedule.updated_at.isoformat() if schedule.updated_at else None,
        next_run=scheduler_status.get("next_run"),
        subscribed_users_count=subscribed_count,
    )


@router.put("/reports/schedule", response_model=ReportScheduleResponse)
async def update_report_schedule(
    data: UpdateScheduleRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update report schedule configuration.

    Admin only endpoint.
    """
    from app.services.scheduler_service import reschedule_reports

    # Get or create schedule record
    result = await db.execute(select(ReportSchedule).where(ReportSchedule.id == 1))
    schedule = result.scalar_one_or_none()

    if not schedule:
        schedule = ReportSchedule(id=1)
        db.add(schedule)

    # Update fields if provided
    if data.enabled is not None:
        schedule.enabled = data.enabled
    if data.schedule_type is not None:
        schedule.schedule_type = data.schedule_type
    if data.day_of_week is not None:
        schedule.day_of_week = data.day_of_week
    if data.hour is not None:
        schedule.hour = data.hour
    if data.minute is not None:
        schedule.minute = data.minute

    schedule.updated_by = admin.id

    await db.commit()
    await db.refresh(schedule)

    # Reschedule the job with new settings
    reschedule_reports(schedule)

    logger.info(
        f"Admin {admin.email} updated report schedule: "
        f"enabled={schedule.enabled}, type={schedule.schedule_type}, "
        f"day={schedule.day_of_week}, time={schedule.hour:02d}:{schedule.minute:02d}"
    )

    # Count subscribed users
    count_result = await db.execute(
        select(func.count(User.id)).where(User.receive_reports == True)  # noqa: E712
    )
    subscribed_count = count_result.scalar() or 0

    # Get updated scheduler status
    from app.services.scheduler_service import get_scheduler_status

    scheduler_status = get_scheduler_status()

    return ReportScheduleResponse(
        enabled=schedule.enabled,
        schedule_type=schedule.schedule_type,
        day_of_week=schedule.day_of_week,
        hour=schedule.hour,
        minute=schedule.minute,
        updated_at=schedule.updated_at.isoformat() if schedule.updated_at else None,
        next_run=scheduler_status.get("next_run"),
        subscribed_users_count=subscribed_count,
    )


# ============================================================================
# Report Subscribers Management
# ============================================================================


class ReportSubscriberItem(BaseModel):
    """User subscribed to reports."""

    id: str
    email: str | None
    display_name: str | None
    role: str


class ReportSubscribersResponse(BaseModel):
    """Response for report subscribers list."""

    subscribers: list[ReportSubscriberItem]
    total: int


@router.get("/reports/subscribers", response_model=ReportSubscribersResponse)
async def get_report_subscribers(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of users subscribed to receive reports.

    Admin only endpoint.
    """
    result = await db.execute(
        select(User).where(User.receive_reports == True).order_by(User.email)  # noqa: E712
    )
    users = result.scalars().all()

    subscribers = [
        ReportSubscriberItem(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            role=user.role,
        )
        for user in users
    ]

    return ReportSubscribersResponse(
        subscribers=subscribers,
        total=len(subscribers),
    )
