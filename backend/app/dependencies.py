"""FastAPI dependencies for the application."""

from typing import Annotated
from uuid import uuid4

from fastapi import Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.jwt_service import jwt_service

# Cookie configuration
USER_ID_COOKIE = "stupidbot_user_id"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 year in seconds


async def get_or_create_user_id(request: Request, response: Response) -> str:
    """
    Get or create a user ID from cookies.

    This provides anonymous user identification without requiring authentication.
    A UUID is generated on first visit and stored in an HTTP-only cookie.

    Args:
        request: The incoming request (to read existing cookie)
        response: The outgoing response (to set new cookie if needed)

    Returns:
        The user ID (existing or newly created)
    """
    user_id = request.cookies.get(USER_ID_COOKIE)

    if not user_id:
        user_id = str(uuid4())
        response.set_cookie(
            key=USER_ID_COOKIE,
            value=user_id,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=False,  # Set to True in production with HTTPS
        )

    return user_id


def get_user_id_from_cookie(request: Request) -> str | None:
    """
    Get user ID from cookies without creating a new one.

    Used for WebSocket connections where we can't set cookies.

    Args:
        request: The incoming request

    Returns:
        The user ID if exists, None otherwise
    """
    return request.cookies.get(USER_ID_COOKIE)


async def get_current_user_required(
    access_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user or raise 401.

    This is a dependency that requires authentication.
    Use this for protected endpoints.

    Raises:
        HTTPException: 401 if not authenticated
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user_id = jwt_service.get_user_id_from_token(access_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Import here to avoid circular imports
    from app.services.auth_service import AuthService

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is blocked",
        )

    return user


async def require_admin(
    current_user: User = Depends(get_current_user_required),
) -> User:
    """
    Require admin role for the current user.

    Use this dependency for admin-only endpoints.

    Raises:
        HTTPException: 403 if user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user
