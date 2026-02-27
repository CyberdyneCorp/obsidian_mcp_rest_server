"""Graph schemas."""

from uuid import UUID

from pydantic import BaseModel

from app.api.schemas.document import DocumentSummaryResponse


class ConnectionResponse(BaseModel):
    """Graph connection response."""

    document: DocumentSummaryResponse
    distance: int
    link_type: str


class GraphResponse(BaseModel):
    """Graph query response."""

    center: DocumentSummaryResponse
    connections: list[ConnectionResponse]


class PathNodeResponse(BaseModel):
    """Node in a path response."""

    id: UUID
    title: str
    path: str


class PathResponse(BaseModel):
    """Shortest path response."""

    path: list[PathNodeResponse]
    length: int
