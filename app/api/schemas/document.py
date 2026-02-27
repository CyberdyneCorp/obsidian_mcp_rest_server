"""Document schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """Document creation request."""

    path: str = Field(min_length=1, max_length=500)
    content: str
    frontmatter: dict[str, Any] | None = None


class DocumentUpdate(BaseModel):
    """Document update request."""

    content: str | None = None
    frontmatter: dict[str, Any] | None = None


class DocumentResponse(BaseModel):
    """Full document response."""

    id: UUID
    title: str
    path: str
    content: str
    frontmatter: dict[str, Any]
    tags: list[str]
    aliases: list[str]
    word_count: int
    link_count: int
    backlink_count: int
    created_at: datetime
    updated_at: datetime


class DocumentSummaryResponse(BaseModel):
    """Document summary response (without content)."""

    id: UUID
    title: str
    path: str
    word_count: int
    link_count: int
    backlink_count: int
    tags: list[str]
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """Document list response."""

    documents: list[DocumentSummaryResponse]
    total: int
    limit: int
    offset: int
