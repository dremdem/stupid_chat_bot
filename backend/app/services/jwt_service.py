"""JWT token service for authentication."""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import settings


class JWTService:
    """Service for creating and validating JWT tokens."""

    def __init__(self):
        """Initialize JWT service with configuration."""
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days

    def create_access_token(
        self,
        user_id: uuid.UUID,
        role: str,
        additional_claims: dict[str, Any] | None = None,
    ) -> str:
        """
        Create a short-lived access token.

        Args:
            user_id: The user's UUID.
            role: The user's role (user, admin, etc.).
            additional_claims: Optional additional JWT claims.

        Returns:
            Encoded JWT access token.
        """
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": str(user_id),
            "role": role,
            "type": "access",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self) -> tuple[str, str, datetime]:
        """
        Create a long-lived refresh token.

        Returns:
            Tuple of (raw_token, hashed_token, expires_at).
            Store the hashed_token in database, return raw_token to client.
        """
        # Generate a cryptographically secure random token
        raw_token = secrets.token_urlsafe(32)

        # Hash the token for database storage
        hashed_token = self._hash_token(raw_token)

        # Calculate expiration
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)

        return raw_token, hashed_token, expires_at

    def verify_access_token(self, token: str) -> dict[str, Any] | None:
        """
        Verify and decode an access token.

        Args:
            token: The JWT access token to verify.

        Returns:
            Token payload if valid, None otherwise.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verify it's an access token
            if payload.get("type") != "access":
                return None

            return payload
        except JWTError:
            return None

    def verify_refresh_token(self, raw_token: str, stored_hash: str) -> bool:
        """
        Verify a refresh token against its stored hash.

        Args:
            raw_token: The raw refresh token from the client.
            stored_hash: The hashed token from the database.

        Returns:
            True if the token matches, False otherwise.
        """
        return self._hash_token(raw_token) == stored_hash

    def _hash_token(self, token: str) -> str:
        """
        Hash a token for secure storage.

        Args:
            token: The raw token to hash.

        Returns:
            SHA-256 hash of the token.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def get_user_id_from_token(self, token: str) -> uuid.UUID | None:
        """
        Extract user ID from an access token.

        Args:
            token: The JWT access token.

        Returns:
            User UUID if valid, None otherwise.
        """
        payload = self.verify_access_token(token)
        if payload and "sub" in payload:
            try:
                return uuid.UUID(payload["sub"])
            except ValueError:
                return None
        return None


# Global instance
jwt_service = JWTService()
