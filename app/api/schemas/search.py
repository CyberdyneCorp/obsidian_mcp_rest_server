"""Search schemas."""


from pydantic import BaseModel, Field

from app.api.schemas.document import DocumentSummaryResponse


class SemanticSearchRequest(BaseModel):
    """Semantic search request."""

    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    folder: str | None = None
    tags: list[str] | None = None


class SearchResultResponse(BaseModel):
    """Search result response."""

    document: DocumentSummaryResponse
    score: float
    matched_chunk: str | None = None


class SemanticSearchResponse(BaseModel):
    """Semantic search response."""

    results: list[SearchResultResponse]
    query: str
    total: int


class FulltextSearchResult(BaseModel):
    """Full-text search result."""

    document: DocumentSummaryResponse
    headline: str | None = None


class FulltextSearchResponse(BaseModel):
    """Full-text search response."""

    results: list[FulltextSearchResult]
    query: str
