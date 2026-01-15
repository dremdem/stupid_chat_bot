"""Authentication API endpoints for OAuth and token management."""

import logging
import secrets
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.jwt_service import jwt_service
from app.services.oauth_service import oauth_service
from app.services.password_service import validate_password_strength
from app.services.verification_service import VerificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Cookie settings
COOKIE_SECURE = False  # Set to True in production with HTTPS
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "lax"
COOKIE_MAX_AGE_ACCESS = 30 * 60  # 30 minutes
COOKIE_MAX_AGE_REFRESH = 7 * 24 * 60 * 60  # 7 days


class TokenResponse(BaseModel):
    """Response containing authentication tokens."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class ProvidersResponse(BaseModel):
    """Response containing available OAuth providers."""

    providers: list[str]


class UserResponse(BaseModel):
    """Response containing user info."""

    user: dict | None
    authenticated: bool


class RegisterRequest(BaseModel):
    """Request for email/password registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    """Request for email/password login."""

    email: EmailStr
    password: str


class AuthMethodsResponse(BaseModel):
    """Response containing available authentication methods."""

    oauth_providers: list[str]
    email_password_enabled: bool = True


class VerifyEmailRequest(BaseModel):
    """Request for email verification."""

    token: str


class VerifyEmailResponse(BaseModel):
    """Response for email verification."""

    success: bool
    message: str
    user: dict | None = None


class ResendVerificationResponse(BaseModel):
    """Response for resend verification request."""

    success: bool
    message: str


@router.get("/methods", response_model=AuthMethodsResponse)
async def get_auth_methods():
    """Get all available authentication methods."""
    return AuthMethodsResponse(
        oauth_providers=oauth_service.get_configured_providers(),
        email_password_enabled=True,
    )


@router.get("/providers", response_model=ProvidersResponse)
async def get_providers():
    """Get list of configured OAuth providers."""
    return ProvidersResponse(providers=oauth_service.get_configured_providers())


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    request: Request,
    access_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current authenticated user.
    """
    if not access_token:
        return UserResponse(user=None, authenticated=False)

    user_id = jwt_service.get_user_id_from_token(access_token)
    if not user_id:
        return UserResponse(user=None, authenticated=False)

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)

    if not user:
        return UserResponse(user=None, authenticated=False)

    # Return blocked users as authenticated so they can see their status and log out
    return UserResponse(
        user=user.to_dict(include_sensitive=True),
        authenticated=True,
    )


@router.post("/register", response_model=TokenResponse)
async def register(
    request: Request,
    response: Response,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user with email and password.

    Returns access token and sets cookies on success.
    """
    # Validate password strength
    is_valid, error_msg = validate_password_strength(data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    auth_service = AuthService(db)

    # Try to register
    user = await auth_service.register_with_email(
        email=data.email,
        password=data.password,
        display_name=data.display_name,
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered. Please login or use a different email.",
        )

    # Handle post-login tasks (admin promotion, etc.)
    await auth_service.handle_user_login(user)

    # Send verification email (async, don't block registration)
    verification_service = VerificationService(db)
    await verification_service.send_verification_email(user)

    # Create auth session
    user_agent = request.headers.get("User-Agent")
    client_ip = request.client.host if request.client else None
    access_token, refresh_token = await auth_service.create_auth_session(
        user=user,
        user_agent=user_agent,
        ip_address=client_ip,
    )

    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=COOKIE_MAX_AGE_ACCESS,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=COOKIE_MAX_AGE_REFRESH,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/api/auth",
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=user.to_dict(include_sensitive=True),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    response: Response,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password.

    Returns access token and sets cookies on success.
    """
    auth_service = AuthService(db)

    # Try to authenticate
    user = await auth_service.authenticate_with_email(
        email=data.email,
        password=data.password,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    # Handle post-login tasks (admin promotion, etc.)
    await auth_service.handle_user_login(user)

    # Create auth session
    user_agent = request.headers.get("User-Agent")
    client_ip = request.client.host if request.client else None
    access_token, refresh_token = await auth_service.create_auth_session(
        user=user,
        user_agent=user_agent,
        ip_address=client_ip,
    )

    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=COOKIE_MAX_AGE_ACCESS,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=COOKIE_MAX_AGE_REFRESH,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/api/auth",
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=user.to_dict(include_sensitive=True),
    )


@router.get("/{provider}")
async def oauth_login(
    provider: str,
    request: Request,
    redirect_url: str | None = Query(default=None),
):
    """
    Initiate OAuth login flow.

    Redirects the user to the OAuth provider's authorization page.
    """
    if not oauth_service.is_provider_configured(provider):
        raise HTTPException(status_code=400, detail=f"Provider '{provider}' is not configured")

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state in session (or use signed cookie)
    # For simplicity, we'll encode the redirect URL in the state
    if redirect_url:
        state = f"{state}:{redirect_url}"

    # Build callback URL using configured backend URL
    # (not request.url_for which uses Docker internal hostname)
    callback_url = f"{settings.backend_url}/api/auth/{provider}/callback"

    # Get authorization URL
    auth_url, _ = await oauth_service.get_authorization_url(
        provider=provider,
        redirect_uri=callback_url,
        state=state,
    )

    # Return redirect URL for frontend to navigate
    return {"authorization_url": auth_url}


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    request: Request,
    response: Response,
    code: str = Query(...),
    state: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle OAuth callback from provider.

    Exchanges the authorization code for tokens and creates/updates user.
    """
    if not oauth_service.is_provider_configured(provider):
        raise HTTPException(status_code=400, detail=f"Provider '{provider}' is not configured")

    # Build callback URL using configured backend URL
    # (must match what was used in authorization request)
    callback_url = f"{settings.backend_url}/api/auth/{provider}/callback"

    try:
        # Exchange code for user info
        user_info = await oauth_service.handle_callback(
            provider=provider,
            code=code,
            redirect_uri=callback_url,
        )
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        # Redirect to frontend with error
        error_redirect = f"{settings.frontend_url}/login?error=oauth_failed"
        return Response(
            status_code=302,
            headers={"Location": error_redirect},
        )

    # Get or create user
    auth_service = AuthService(db)
    user = await auth_service.get_or_create_oauth_user(user_info)

    # Allow blocked users to authenticate so they can see their status and log out
    if user.is_blocked:
        logger.info(f"Blocked user logged in via OAuth: {user.email or user.id}")

    # Handle post-login tasks (admin promotion, etc.)
    await auth_service.handle_user_login(user)

    # Create auth session
    user_agent = request.headers.get("User-Agent")
    client_ip = request.client.host if request.client else None
    access_token, refresh_token = await auth_service.create_auth_session(
        user=user,
        user_agent=user_agent,
        ip_address=client_ip,
    )

    # Parse redirect URL from state
    redirect_url = settings.frontend_url
    if state and ":" in state:
        _, custom_redirect = state.split(":", 1)
        if custom_redirect.startswith(settings.frontend_url):
            redirect_url = custom_redirect

    # Set tokens as HTTP-only cookies
    response = Response(
        status_code=302,
        headers={"Location": redirect_url},
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=COOKIE_MAX_AGE_ACCESS,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=COOKIE_MAX_AGE_REFRESH,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/api/auth",  # Only sent to auth endpoints
    )

    return response


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: Request,
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    Implements token rotation - old refresh token is invalidated.
    """
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token provided")

    auth_service = AuthService(db)
    user_agent = request.headers.get("User-Agent")
    client_ip = request.client.host if request.client else None

    result = await auth_service.refresh_tokens(
        refresh_token=refresh_token,
        user_agent=user_agent,
        ip_address=client_ip,
    )

    if not result:
        # Clear invalid cookies
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token", path="/api/auth")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    new_access_token, new_refresh_token = result

    # Get user info for response
    user_id = jwt_service.get_user_id_from_token(new_access_token)
    user = await auth_service.get_user_by_id(user_id) if user_id else None

    # Set new cookies
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        max_age=COOKIE_MAX_AGE_ACCESS,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        max_age=COOKIE_MAX_AGE_REFRESH,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/api/auth",
    )

    return TokenResponse(
        access_token=new_access_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=user.to_dict(include_sensitive=True) if user else {},
    )


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Logout user by invalidating refresh token.
    """
    if refresh_token:
        auth_service = AuthService(db)
        await auth_service.logout(refresh_token)

    # Clear cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/api/auth")

    return {"message": "Logged out successfully"}


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify email using token from verification link.

    Marks user's email as verified if token is valid.
    """
    verification_service = VerificationService(db)
    user = await verification_service.verify_token(data.token)

    if not user:
        return VerifyEmailResponse(
            success=False,
            message="Invalid or expired verification link. Please request a new one.",
        )

    return VerifyEmailResponse(
        success=True,
        message="Email verified successfully!",
        user=user.to_dict(include_sensitive=True),
    )


@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(
    access_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Resend verification email to the current user.

    Rate-limited to prevent abuse.
    """
    if not access_token:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_id = jwt_service.get_user_id_from_token(access_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_email_verified:
        return ResendVerificationResponse(
            success=False,
            message="Email is already verified.",
        )

    verification_service = VerificationService(db)

    # Check rate limit
    can_resend, seconds_remaining = await verification_service.can_resend_verification(user)
    if not can_resend:
        return ResendVerificationResponse(
            success=False,
            message=f"Please wait {seconds_remaining} seconds before requesting another email.",
        )

    # Send verification email
    success = await verification_service.send_verification_email(user)

    if success:
        return ResendVerificationResponse(
            success=True,
            message="Verification email sent! Check your inbox.",
        )
    else:
        return ResendVerificationResponse(
            success=False,
            message="Failed to send email. Please try again later.",
        )
