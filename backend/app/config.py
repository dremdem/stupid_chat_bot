"""Application configuration using pydantic-settings."""

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
