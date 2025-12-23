"""FastAPI dependencies for the application."""

from uuid import uuid4

from fastapi import Request, Response

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
