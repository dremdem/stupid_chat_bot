"""Pydantic schemas for User-related API operations."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    """User role enumeration for access control."""

    ANONYMOUS = "anonymous"
    USER = "user"
    UNLIMITED = "unlimited"
    ADMIN = "admin"


class AuthProvider(str, Enum):
    """Authentication provider enumeration."""

    EMAIL = "email"
    GOOGLE = "google"
    GITHUB = "github"
    FACEBOOK = "facebook"


# --- Base Schemas ---


class UserBase(BaseModel):
    """Base schema with common user fields."""

    email: EmailStr | None = None
    display_name: str | None = Field(None, max_length=100)
    avatar_url: str | None = Field(None, max_length=500)


class UserCreate(UserBase):
    """Schema for creating a new user via email registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    display_name: str | None = Field(None, max_length=100)


class UserCreateOAuth(BaseModel):
    """Schema for creating a user via OAuth provider."""

    email: EmailStr | None = None
    display_name: str | None = Field(None, max_length=100)
    avatar_url: str | None = Field(None, max_length=500)
    provider: AuthProvider
    provider_id: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    display_name: str | None = Field(None, max_length=100)
    avatar_url: str | None = Field(None, max_length=500)


class UserUpdateAdmin(BaseModel):
    """Schema for admin updating any user field."""

    display_name: str | None = Field(None, max_length=100)
    avatar_url: str | None = Field(None, max_length=500)
    role: UserRole | None = None
    message_limit: int | None = Field(None, ge=0)
    context_window_size: int | None = Field(None, ge=1, le=100)
    is_blocked: bool | None = None


# --- Response Schemas ---


class UserPublic(BaseModel):
    """Public user info visible to other users."""

    id: UUID
    display_name: str | None
    avatar_url: str | None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """User info returned in API responses (for authenticated user)."""

    id: UUID
    email: str | None
    display_name: str | None
    avatar_url: str | None
    provider: str
    role: str
    message_limit: int | None
    context_window_size: int
    is_blocked: bool
    is_email_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """User schema with all database fields (internal use only)."""

    password_hash: str | None
    provider_id: str | None

    model_config = ConfigDict(from_attributes=True)


# --- Admin Schemas ---


class UserAdminResponse(UserResponse):
    """Extended user info for admin views."""

    provider_id: str | None

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Response for paginated user list."""

    users: list[UserAdminResponse]
    total: int
    limit: int
    offset: int


# --- Message Limit Schemas ---


class MessageLimitInfo(BaseModel):
    """Information about user's message limits."""

    limit: int | None  # None means unlimited
    used: int
    remaining: int | None  # None means unlimited
    is_unlimited: bool
