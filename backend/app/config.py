"""Application configuration using pydantic-settings."""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # CORS Configuration
    cors_origins: str = "http://localhost:5173"

    # AI Configuration
    ai_provider: str = "anthropic"  # Options: anthropic, openai, google, meta, deepseek
    ai_model: str = ""  # Optional: Override default model for provider

    # Provider-specific API keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    # Database Configuration
    database_path: str = "data/chat.db"  # Relative to project root
    database_echo: bool = False  # Enable SQL logging for debugging

    # OAuth Configuration
    google_client_id: str = ""
    google_client_secret: str = ""
    # GitHub OAuth: Support both GITHUB_ and GH_ prefixes
    # (GITHUB_ is reserved in GitHub Actions secrets)
    github_client_id: str = Field(
        default="",
        validation_alias=AliasChoices("github_client_id", "gh_client_id"),
    )
    github_client_secret: str = Field(
        default="",
        validation_alias=AliasChoices("github_client_secret", "gh_client_secret"),
    )
    facebook_client_id: str = ""
    facebook_client_secret: str = ""

    # JWT Configuration
    jwt_secret_key: str = "change-me-in-production"  # MUST be changed in production
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Admin Bootstrap
    initial_admin_email: str = ""  # User with this email auto-promoted to admin

    # Frontend URL for OAuth redirects
    frontend_url: str = "http://localhost:5173"

    # Backend URL for OAuth callbacks (external URL, not Docker internal)
    backend_url: str = "http://localhost:8000"

    @property
    def database_url(self) -> str:
        """Get database URL for SQLAlchemy."""
        return f"sqlite+aiosqlite:///{self.database_path}"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def selected_model(self) -> str:
        """Get the model name based on provider and configuration."""
        if self.ai_model:
            return self.ai_model

        # Provider defaults
        defaults = {
            "anthropic": "claude-3-5-sonnet-20241022",
            "openai": "gpt-4-turbo",
            "google": "gemini-1.5-pro",
            "meta": "llama-3.1-70b",
            "deepseek": "deepseek-chat",
        }
        return defaults.get(self.ai_provider, "claude-3-5-sonnet-20241022")


# Global settings instance
settings = Settings()
