"""Pydantic schemas for message limits API responses."""

from pydantic import BaseModel


class MessageLimitResponse(BaseModel):
    """Response containing message limit information."""

    limit: int | None  # None means unlimited
    used: int
    remaining: int | None  # None means unlimited
    is_unlimited: bool
    can_send: bool
    user_role: str


class LimitExceededResponse(BaseModel):
    """Response when message limit is exceeded."""

    error: str = "message_limit_exceeded"
    message: str
    limit_info: MessageLimitResponse
    login_required: bool = True
    contact_url: str | None = None  # For users who need extended access
