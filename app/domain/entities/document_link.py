"""DocumentLink entity representing a link between documents."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class LinkType(str, Enum):
    """Type of document link."""

    WIKILINK = "wikilink"  # [[Target]]
    EMBED = "embed"  # ![[Target]]
    HEADER = "header"  # [[Target#Heading]]
    BLOCK = "block"  # [[Target#^block-id]]


@dataclass
class DocumentLink:
    """DocumentLink entity representing a wiki-style link between documents.

    This tracks both resolved and unresolved links. Unresolved links
    have target_document_id = None and is_resolved = False.
    """

    id: UUID = field(default_factory=uuid4)
    vault_id: UUID = field(default_factory=uuid4)
    source_document_id: UUID = field(default_factory=uuid4)
    target_document_id: UUID | None = None
    link_text: str = ""  # Original text (e.g., "Target Document")
    display_text: str | None = None  # Custom display (from [[Target|Display]])
    link_type: LinkType = LinkType.WIKILINK
    is_resolved: bool = False
    position_start: int | None = None  # Character offset in source
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Set display text to link text if not provided."""
        if self.display_text is None:
            self.display_text = self.link_text

    def resolve(self, target_document_id: UUID) -> None:
        """Mark this link as resolved to a target document."""
        self.target_document_id = target_document_id
        self.is_resolved = True

    def unresolve(self) -> None:
        """Mark this link as unresolved."""
        self.target_document_id = None
        self.is_resolved = False

    @property
    def effective_display_text(self) -> str:
        """Get the display text (custom or link text)."""
        return self.display_text or self.link_text

    @classmethod
    def create(
        cls,
        vault_id: UUID,
        source_document_id: UUID,
        link_text: str,
        display_text: str | None = None,
        link_type: LinkType = LinkType.WIKILINK,
        position_start: int | None = None,
        target_document_id: UUID | None = None,
    ) -> "DocumentLink":
        """Factory method to create a new document link."""
        return cls(
            vault_id=vault_id,
            source_document_id=source_document_id,
            target_document_id=target_document_id,
            link_text=link_text,
            display_text=display_text,
            link_type=link_type,
            is_resolved=target_document_id is not None,
            position_start=position_start,
        )
