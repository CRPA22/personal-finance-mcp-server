"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/finance_mcp"

    # Logging
    log_level: str = "INFO"

    # Default user for Phase 2 (no auth) - UUID from migration 002
    default_user_id: str = "00000000-0000-0000-0000-000000000001"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24


settings = Settings()
