"""Environment configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    gemini_api_key: str | None = None

    # Database
    database_url: str = "sqlite:///fiscal_documents.db"

    # Storage
    archive_dir: str = "./archives"

    # Logging
    log_level: str = "INFO"
    redact_pii: bool = True  # Redact PII in logs by default

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
