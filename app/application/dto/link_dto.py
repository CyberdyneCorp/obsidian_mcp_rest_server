"""Link DTOs."""

from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.document_link import DocumentLink


@dataclass
class LinkTargetDTO:
    """DTO for link target document info."""

    id: UUID
    title: str
    path: str


@dataclass
class LinkDTO:
    """DTO for a document link."""

    id: UUID
    link_text: str
    display_text: str | None
    link_type: str
    is_resolved: bool
    target_document: LinkTargetDTO | None

    @classmethod
    def from_entity(
        cls,
        link: DocumentLink,
        target_title: str | None = None,
        target_path: str | None = None,
    ) -> "LinkDTO":
        """Create DTO from entity."""
        target = None
        if link.target_document_id and target_title and target_path:
            target = LinkTargetDTO(
                id=link.target_document_id,
                title=target_title,
                path=target_path,
            )

        return cls(
            id=link.id,
            link_text=link.link_text,
            display_text=link.display_text,
            link_type=link.link_type.value,
            is_resolved=link.is_resolved,
            target_document=target,
        )


@dataclass
class BacklinkSourceDTO:
    """DTO for backlink source document info."""

    id: UUID
    title: str
    path: str


@dataclass
class BacklinkDTO:
    """DTO for a backlink."""

    document: BacklinkSourceDTO
    link_text: str
    context: str | None = None  # Surrounding text

    @classmethod
    def from_link(
        cls,
        link: DocumentLink,
        source_title: str,
        source_path: str,
        context: str | None = None,
    ) -> "BacklinkDTO":
        """Create DTO from link and source info."""
        return cls(
            document=BacklinkSourceDTO(
                id=link.source_document_id,
                title=source_title,
                path=source_path,
            ),
            link_text=link.link_text,
            context=context,
        )
