"""Search DTOs."""

from dataclasses import dataclass, field

from app.application.dto.document_dto import DocumentSummaryDTO


@dataclass
class SearchQueryDTO:
    """DTO for search query parameters."""

    query: str
    limit: int = 10
    threshold: float = 0.7
    folder: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class SearchResultDTO:
    """DTO for a single search result."""

    document: DocumentSummaryDTO
    score: float
    matched_chunk: str | None = None


@dataclass
class FulltextSearchResultDTO:
    """DTO for fulltext search result."""

    document: DocumentSummaryDTO
    headline: str | None = None
