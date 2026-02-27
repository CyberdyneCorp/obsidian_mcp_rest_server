"""Vault schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class VaultCreate(BaseModel):
    """Vault creation request."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class VaultUpdate(BaseModel):
    """Vault update request."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class VaultResponse(BaseModel):
    """Vault response."""

    id: UUID
    name: str
    slug: str
    description: str | None
    document_count: int
    created_at: datetime
    updated_at: datetime


class VaultListResponse(BaseModel):
    """Vault list response."""

    vaults: list[VaultResponse]
