"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://obsidian:obsidian@localhost:5433/obsidian",
        description="PostgreSQL connection string (async)",
    )

    # OpenAI
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for embeddings",
    )
    embedding_model: str = Field(
        default="text-embedding-ada-002",
        description="OpenAI embedding model",
    )
    embedding_dimensions: int = Field(
        default=1536,
        description="Embedding vector dimensions",
    )

    # JWT Authentication
    jwt_secret: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT signing",
    )
    jwt_issuer: str = Field(
        default="obsidian-vault-server",
        description="Expected JWT issuer claim",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    access_token_expire_minutes: int = Field(
        default=60,
        description="Access token expiry in minutes",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiry in days",
    )

    # Server
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    debug: bool = Field(
        default=False,
        description="Debug mode",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed CORS origins",
    )

    # Storage
    storage_path: str = Field(
        default="./storage",
        description="Path for file storage",
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting",
    )

    # Chunking
    chunk_size: int = Field(
        default=500,
        description="Token size for document chunks",
    )
    chunk_overlap: int = Field(
        default=50,
        description="Token overlap between chunks",
    )
    max_upload_size_mb: int = Field(
        default=100,
        ge=1,
        description="Maximum upload size in MB",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str] | Any:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                # Let pydantic parse JSON-style list in normal flow.
                return value
            return [origin.strip() for origin in raw.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        """Validate security settings when running in production."""
        if self.environment == "production":
            if self.jwt_secret == "change-me-in-production":
                raise ValueError("JWT_SECRET must be configured in production")
            if len(self.jwt_secret) < 32:
                raise ValueError("JWT_SECRET must be at least 32 characters in production")
            if "*" in self.cors_origins:
                raise ValueError("CORS_ORIGINS cannot include '*' in production")
        return self

    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL for Alembic."""
        return self.database_url.replace("+asyncpg", "")

    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
