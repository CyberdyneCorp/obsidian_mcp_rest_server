"""Document DTOs."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.entities.document import Document


@dataclass
class DocumentDTO:
    """Document data transfer object."""

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

    @classmethod
    def from_entity(cls, document: Document) -> "DocumentDTO":
        """Create DTO from entity."""
        return cls(
            id=document.id,
            title=document.title,
            path=document.path,
            content=document.content,
            frontmatter=document.frontmatter.to_dict(),
            tags=list(document.frontmatter.tags),
            aliases=document.aliases,
            word_count=document.word_count,
            link_count=document.link_count,
            backlink_count=document.backlink_count,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )


@dataclass
class DocumentSummaryDTO:
    """Document summary DTO (without full content)."""

    id: UUID
    title: str
    path: str
    word_count: int
    link_count: int
    backlink_count: int
    tags: list[str]
    updated_at: datetime

    @classmethod
    def from_entity(cls, document: Document) -> "DocumentSummaryDTO":
        """Create DTO from entity."""
        return cls(
            id=document.id,
            title=document.title,
            path=document.path,
            word_count=document.word_count,
            link_count=document.link_count,
            backlink_count=document.backlink_count,
            tags=list(document.frontmatter.tags),
            updated_at=document.updated_at,
        )


@dataclass
class DocumentCreateDTO:
    """DTO for creating a document."""

    path: str
    content: str
    frontmatter: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentUpdateDTO:
    """DTO for updating a document."""

    content: str | None = None
    frontmatter: dict[str, Any] | None = None
