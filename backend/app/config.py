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
    ai_provider: str = "anthropic"
    anthropic_api_key: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
