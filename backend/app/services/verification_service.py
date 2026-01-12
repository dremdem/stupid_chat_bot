"""Email verification token service."""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.email_verification import EmailVerificationToken
from app.models.user import User
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class VerificationService:
    """Service for managing email verification tokens."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a token using SHA-256."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def _generate_token() -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)

    async def create_verification_token(self, user: User) -> str:
        """
        Create a new verification token for a user.

        Invalidates any existing tokens for the user.

        Args:
            user: The user to create a token for.

        Returns:
            The raw token (not hashed).
        """
        # Invalidate existing tokens for this user
        await self._invalidate_user_tokens(user.id)

        # Generate new token
        raw_token = self._generate_token()
        token_hash = self._hash_token(raw_token)

        # Calculate expiration
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.email_verification_token_expire_hours
        )

        # Create token record
        token = EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(token)
        await self.db.commit()

        logger.info(f"Created verification token for user {user.id}")
        return raw_token

    async def verify_token(self, raw_token: str) -> User | None:
        """
        Verify a token and mark the user's email as verified.

        Args:
            raw_token: The raw token from the verification link.

        Returns:
            The verified user if successful, None otherwise.
        """
        token_hash = self._hash_token(raw_token)

        # Find token
        result = await self.db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash,
                EmailVerificationToken.is_used == False,  # noqa: E712
            )
        )
        token = result.scalar_one_or_none()

        if not token:
            logger.warning("Verification token not found or already used")
            return None

        # Check expiration (add timezone for SQLite compatibility)
        expires_at = token.expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            logger.warning(f"Verification token expired for user {token.user_id}")
            return None

        # Get user
        user_result = await self.db.execute(select(User).where(User.id == token.user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            logger.error(f"User not found for verification token: {token.user_id}")
            return None

        # Mark token as used
        token.is_used = True

        # Mark user email as verified
        user.is_email_verified = True

        await self.db.commit()
        logger.info(f"Email verified for user {user.id}")

        return user

    async def send_verification_email(self, user: User) -> bool:
        """
        Generate token and send verification email.

        Args:
            user: The user to send verification email to.

        Returns:
            True if email was sent successfully.
        """
        if not user.email:
            logger.error(f"Cannot send verification email: user {user.id} has no email")
            return False

        # Create token
        raw_token = await self.create_verification_token(user)

        # Build verification URL
        verification_url = f"{settings.frontend_url}/verify-email?token={raw_token}"

        # Send email
        success = await email_service.send_verification_email(
            to_email=user.email,
            verification_url=verification_url,
            display_name=user.display_name,
        )

        return success

    async def can_resend_verification(self, user: User) -> tuple[bool, int]:
        """
        Check if a user can request a new verification email.

        Implements rate limiting based on cooldown period.

        Args:
            user: The user requesting resend.

        Returns:
            Tuple of (can_resend, seconds_until_allowed).
        """
        # Find most recent token for user
        result = await self.db.execute(
            select(EmailVerificationToken)
            .where(EmailVerificationToken.user_id == user.id)
            .order_by(EmailVerificationToken.created_at.desc())
            .limit(1)
        )
        latest_token = result.scalar_one_or_none()

        if not latest_token:
            return True, 0

        # Check cooldown
        cooldown_seconds = settings.email_verification_resend_cooldown_seconds
        time_since_created = (
            datetime.now(timezone.utc) - latest_token.created_at.replace(tzinfo=timezone.utc)
        ).total_seconds()

        if time_since_created < cooldown_seconds:
            seconds_remaining = int(cooldown_seconds - time_since_created)
            return False, seconds_remaining

        return True, 0

    async def _invalidate_user_tokens(self, user_id) -> None:
        """Mark all existing tokens for a user as used."""
        result = await self.db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.is_used == False,  # noqa: E712
            )
        )
        tokens = result.scalars().all()

        for token in tokens:
            token.is_used = True

        if tokens:
            await self.db.commit()
            logger.info(f"Invalidated {len(tokens)} existing tokens for user {user_id}")
