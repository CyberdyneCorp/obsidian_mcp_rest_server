"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
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
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    debug: bool = Field(
        default=False,
        description="Debug mode",
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

    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL for Alembic."""
        return self.database_url.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
