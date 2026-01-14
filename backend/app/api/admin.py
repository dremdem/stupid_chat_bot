"""Admin API endpoints for user management."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin
from app.models.message import Message
from app.models.user import User, UserRole

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
