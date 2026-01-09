"""OAuth 2.0 service for provider authentication."""

import logging
from dataclasses import dataclass
from typing import Any

import httpx
from authlib.integrations.starlette_client import OAuth

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class OAuthUserInfo:
    """Standardized user info from OAuth providers."""

    provider: str
    provider_id: str
    email: str | None
    display_name: str | None
    avatar_url: str | None
    raw_data: dict[str, Any]


class OAuthService:
    """Service for handling OAuth authentication with multiple providers."""

    def __init__(self):
        """Initialize OAuth clients for all providers."""
        self.oauth = OAuth()
        self._setup_providers()

    def _setup_providers(self):
        """Configure OAuth providers."""
        # Google OAuth
        if settings.google_client_id and settings.google_client_secret:
            self.oauth.register(
                name="google",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                client_kwargs={"scope": "openid email profile"},
            )
            logger.info("Google OAuth provider configured")

        # GitHub OAuth
        if settings.github_client_id and settings.github_client_secret:
            self.oauth.register(
                name="github",
                client_id=settings.github_client_id,
                client_secret=settings.github_client_secret,
                authorize_url="https://github.com/login/oauth/authorize",
                access_token_url="https://github.com/login/oauth/access_token",
                api_base_url="https://api.github.com/",
                client_kwargs={"scope": "user:email"},
            )
            logger.info("GitHub OAuth provider configured")

        # Facebook OAuth
        if settings.facebook_client_id and settings.facebook_client_secret:
            self.oauth.register(
                name="facebook",
                client_id=settings.facebook_client_id,
                client_secret=settings.facebook_client_secret,
                authorize_url="https://www.facebook.com/v18.0/dialog/oauth",
                access_token_url="https://graph.facebook.com/v18.0/oauth/access_token",
                api_base_url="https://graph.facebook.com/v18.0/",
                client_kwargs={"scope": "email public_profile"},
            )
            logger.info("Facebook OAuth provider configured")

    def is_provider_configured(self, provider: str) -> bool:
        """Check if a provider is configured."""
        # Note: create_client() returns None for unregistered providers,
        # it doesn't raise an exception
        client = self.oauth.create_client(provider)
        return client is not None

    def get_configured_providers(self) -> list[str]:
        """Get list of configured OAuth providers."""
        providers = []
        for provider in ["google", "github", "facebook"]:
            if self.is_provider_configured(provider):
                providers.append(provider)
        return providers

    async def get_authorization_url(
        self,
        provider: str,
        redirect_uri: str,
        state: str | None = None,
    ) -> tuple[str, str]:
        """
        Get the authorization URL for a provider.

        Args:
            provider: OAuth provider name (google, github, facebook).
            redirect_uri: URL to redirect to after authorization.
            state: Optional state parameter for CSRF protection.

        Returns:
            Tuple of (authorization_url, state).
        """
        client = self.oauth.create_client(provider)

        # For providers that don't support PKCE, we just need the URL
        if provider == "google":
            # Google uses OpenID Connect
            url = await client.create_authorization_url(redirect_uri, state=state)
            return url["url"], url.get("state", state)
        else:
            # GitHub and Facebook use standard OAuth2
            url = await client.create_authorization_url(redirect_uri, state=state)
            return url["url"], url.get("state", state)

    async def handle_callback(
        self,
        provider: str,
        code: str,
        redirect_uri: str,
    ) -> OAuthUserInfo:
        """
        Handle OAuth callback and get user info.

        Args:
            provider: OAuth provider name.
            code: Authorization code from the provider.
            redirect_uri: The redirect URI used in the authorization request.

        Returns:
            Standardized user info.
        """
        # Exchange code for token
        async with httpx.AsyncClient() as http_client:
            if provider == "google":
                token = await self._exchange_google_token(http_client, code, redirect_uri)
                return await self._get_google_user_info(http_client, token)

            elif provider == "github":
                token = await self._exchange_github_token(http_client, code, redirect_uri)
                return await self._get_github_user_info(http_client, token)

            elif provider == "facebook":
                token = await self._exchange_facebook_token(http_client, code, redirect_uri)
                return await self._get_facebook_user_info(http_client, token)

            else:
                raise ValueError(f"Unsupported provider: {provider}")

    async def _exchange_google_token(
        self,
        http_client: httpx.AsyncClient,
        code: str,
        redirect_uri: str,
    ) -> dict:
        """Exchange Google authorization code for access token."""
        response = await http_client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        return response.json()

    async def _get_google_user_info(
        self,
        http_client: httpx.AsyncClient,
        token: dict,
    ) -> OAuthUserInfo:
        """Get user info from Google."""
        response = await http_client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token['access_token']}"},
        )
        response.raise_for_status()
        data = response.json()

        return OAuthUserInfo(
            provider="google",
            provider_id=data["id"],
            email=data.get("email"),
            display_name=data.get("name"),
            avatar_url=data.get("picture"),
            raw_data=data,
        )

    async def _exchange_github_token(
        self,
        http_client: httpx.AsyncClient,
        code: str,
        redirect_uri: str,
    ) -> dict:
        """Exchange GitHub authorization code for access token."""
        response = await http_client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "code": code,
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        return response.json()

    async def _get_github_user_info(
        self,
        http_client: httpx.AsyncClient,
        token: dict,
    ) -> OAuthUserInfo:
        """Get user info from GitHub."""
        headers = {"Authorization": f"Bearer {token['access_token']}"}

        # Get user profile
        response = await http_client.get(
            "https://api.github.com/user",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        # Get user email (might be private)
        email = data.get("email")
        if not email:
            email_response = await http_client.get(
                "https://api.github.com/user/emails",
                headers=headers,
            )
            if email_response.status_code == 200:
                emails = email_response.json()
                # Get primary verified email
                for e in emails:
                    if e.get("primary") and e.get("verified"):
                        email = e["email"]
                        break

        return OAuthUserInfo(
            provider="github",
            provider_id=str(data["id"]),
            email=email,
            display_name=data.get("name") or data.get("login"),
            avatar_url=data.get("avatar_url"),
            raw_data=data,
        )

    async def _exchange_facebook_token(
        self,
        http_client: httpx.AsyncClient,
        code: str,
        redirect_uri: str,
    ) -> dict:
        """Exchange Facebook authorization code for access token."""
        response = await http_client.get(
            "https://graph.facebook.com/v18.0/oauth/access_token",
            params={
                "code": code,
                "client_id": settings.facebook_client_id,
                "client_secret": settings.facebook_client_secret,
                "redirect_uri": redirect_uri,
            },
        )
        response.raise_for_status()
        return response.json()

    async def _get_facebook_user_info(
        self,
        http_client: httpx.AsyncClient,
        token: dict,
    ) -> OAuthUserInfo:
        """Get user info from Facebook."""
        response = await http_client.get(
            "https://graph.facebook.com/v18.0/me",
            params={
                "fields": "id,name,email,picture.type(large)",
                "access_token": token["access_token"],
            },
        )
        response.raise_for_status()
        data = response.json()

        avatar_url = None
        if "picture" in data and "data" in data["picture"]:
            avatar_url = data["picture"]["data"].get("url")

        return OAuthUserInfo(
            provider="facebook",
            provider_id=data["id"],
            email=data.get("email"),
            display_name=data.get("name"),
            avatar_url=avatar_url,
            raw_data=data,
        )


# Global instance
oauth_service = OAuthService()
