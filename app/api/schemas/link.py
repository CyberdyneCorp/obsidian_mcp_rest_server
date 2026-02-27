"""Link schemas."""

from uuid import UUID

from pydantic import BaseModel


class LinkTargetResponse(BaseModel):
    """Link target document info."""

    id: UUID
    title: str
    path: str


class LinkResponse(BaseModel):
    """Link response."""

    id: UUID
    link_text: str
    display_text: str | None
    link_type: str
    is_resolved: bool
    target_document: LinkTargetResponse | None


class LinksResponse(BaseModel):
    """Outgoing links response."""

    links: list[LinkResponse]


class BacklinkSourceResponse(BaseModel):
    """Backlink source document info."""

    id: UUID
    title: str
    path: str


class BacklinkResponse(BaseModel):
    """Backlink response."""

    document: BacklinkSourceResponse
    link_text: str
    context: str | None = None


class BacklinksResponse(BaseModel):
    """Backlinks response."""

    backlinks: list[BacklinkResponse]
