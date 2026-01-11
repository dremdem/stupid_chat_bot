"""Authentication service for user management."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User, UserRole
from app.models.user_session import UserSession
from app.services.jwt_service import jwt_service
from app.services.oauth_service import OAuthUserInfo
from app.services.password_service import hash_password, verify_password

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling user authentication and session management."""

    def __init__(self, db: AsyncSession):
        """Initialize auth service with database session."""
        self.db = db

    async def get_or_create_oauth_user(self, user_info: OAuthUserInfo) -> User:
        """
        Get existing user or create new one from OAuth provider info.

        Args:
            user_info: Standardized user info from OAuth provider.

        Returns:
            The User model instance.
        """
        # Try to find existing user by provider + provider_id
        stmt = select(User).where(
            User.provider == user_info.provider,
            User.provider_id == user_info.provider_id,
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Update user info if changed
            user.display_name = user_info.display_name or user.display_name
            user.avatar_url = user_info.avatar_url or user.avatar_url
            if user_info.email and not user.email:
                user.email = user_info.email
            await self.db.commit()
            logger.info(f"Existing user logged in: {user.email or user.id}")
            return user

        # Try to find existing user by email (link accounts)
        if user_info.email:
            stmt = select(User).where(User.email == user_info.email)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                # Link this OAuth provider to existing account
                user.provider = user_info.provider
                user.provider_id = user_info.provider_id
                user.display_name = user_info.display_name or user.display_name
                user.avatar_url = user_info.avatar_url or user.avatar_url
                await self.db.commit()
                logger.info(f"Linked {user_info.provider} to existing user: {user.email}")
                return user

        # Create new user
        user = User(
            id=uuid.uuid4(),
            email=user_info.email,
            provider=user_info.provider,
            provider_id=user_info.provider_id,
            display_name=user_info.display_name,
            avatar_url=user_info.avatar_url,
            role=UserRole.USER.value,
            is_email_verified=bool(user_info.email),  # OAuth emails are verified
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"New user created via {user_info.provider}: {user.email or user.id}")
        return user

    async def handle_user_login(self, user: User) -> None:
        """
        Handle post-login tasks like admin auto-promotion.

        Args:
            user: The user who just logged in.
        """
        # Check for initial admin promotion
        if (
            settings.initial_admin_email
            and user.email
            and user.email.lower() == settings.initial_admin_email.lower()
        ):
            if user.role != UserRole.ADMIN.value:
                user.role = UserRole.ADMIN.value
                await self.db.commit()
                logger.info(f"Auto-promoted initial admin: {user.email}")

    async def create_auth_session(
        self,
        user: User,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[str, str]:
        """
        Create authentication session with tokens.

        Args:
            user: The authenticated user.
            user_agent: Client user agent string.
            ip_address: Client IP address.

        Returns:
            Tuple of (access_token, refresh_token).
        """
        # Create access token
        access_token = jwt_service.create_access_token(
            user_id=user.id,
            role=user.role,
            additional_claims={
                "email": user.email,
                "display_name": user.display_name,
            },
        )

        # Create refresh token
        raw_refresh_token, hashed_refresh_token, expires_at = jwt_service.create_refresh_token()

        # Store refresh token in database
        session = UserSession(
            id=uuid.uuid4(),
            user_id=user.id,
            refresh_token_hash=hashed_refresh_token,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(session)
        await self.db.commit()

        return access_token, raw_refresh_token

    async def refresh_tokens(
        self,
        refresh_token: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[str, str] | None:
        """
        Refresh access token using refresh token (with rotation).

        Args:
            refresh_token: The raw refresh token.
            user_agent: Client user agent string.
            ip_address: Client IP address.

        Returns:
            Tuple of (new_access_token, new_refresh_token) or None if invalid.
        """
        # Hash the provided token
        token_hash = jwt_service._hash_token(refresh_token)

        # Find the session
        stmt = select(UserSession).where(UserSession.refresh_token_hash == token_hash)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            logger.warning("Refresh token not found")
            return None

        if session.is_expired:
            # Delete expired session
            await self.db.delete(session)
            await self.db.commit()
            logger.warning(f"Refresh token expired for user {session.user_id}")
            return None

        # Get the user
        stmt = select(User).where(User.id == session.user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            await self.db.delete(session)
            await self.db.commit()
            return None

        if user.is_blocked:
            await self.db.delete(session)
            await self.db.commit()
            logger.warning(f"Blocked user attempted token refresh: {user.id}")
            return None

        # Delete old session (token rotation)
        await self.db.delete(session)

        # Create new session
        return await self.create_auth_session(user, user_agent, ip_address)

    async def logout(self, refresh_token: str) -> bool:
        """
        Logout by invalidating refresh token.

        Args:
            refresh_token: The raw refresh token to invalidate.

        Returns:
            True if session was found and deleted, False otherwise.
        """
        token_hash = jwt_service._hash_token(refresh_token)

        stmt = select(UserSession).where(UserSession.refresh_token_hash == token_hash)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            await self.db.delete(session)
            await self.db.commit()
            return True

        return False

    async def logout_all_sessions(self, user_id: uuid.UUID) -> int:
        """
        Logout all sessions for a user.

        Args:
            user_id: The user's ID.

        Returns:
            Number of sessions deleted.
        """
        stmt = select(UserSession).where(UserSession.user_id == user_id)
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        count = len(sessions)
        for session in sessions:
            await self.db.delete(session)

        await self.db.commit()
        return count

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def register_with_email(
        self,
        email: str,
        password: str,
        display_name: str | None = None,
    ) -> User | None:
        """
        Register a new user with email and password.

        Args:
            email: User's email address.
            password: Plain text password (will be hashed).
            display_name: Optional display name.

        Returns:
            The created User or None if email already exists.
        """
        # Check if email already exists
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            logger.warning(f"Registration failed: email already exists: {email}")
            return None

        # Create new user with hashed password
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password(password),
            provider="email",
            display_name=display_name or email.split("@")[0],
            role=UserRole.USER.value,
            is_email_verified=False,  # Email not verified yet
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"New user registered with email: {email}")
        return user

    async def authenticate_with_email(
        self,
        email: str,
        password: str,
    ) -> User | None:
        """
        Authenticate user with email and password.

        Args:
            email: User's email address.
            password: Plain text password to verify.

        Returns:
            The User if authentication succeeds, None otherwise.
        """
        user = await self.get_user_by_email(email)

        if not user:
            logger.warning(f"Login failed: user not found: {email}")
            return None

        if not user.password_hash:
            # User registered via OAuth, no password set
            logger.warning(f"Login failed: no password set for user: {email}")
            return None

        if not verify_password(password, user.password_hash):
            logger.warning(f"Login failed: invalid password for user: {email}")
            return None

        if user.is_blocked:
            logger.warning(f"Login failed: user is blocked: {email}")
            return None

        logger.info(f"User logged in with email: {email}")
        return user
