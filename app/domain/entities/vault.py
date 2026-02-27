"""Vault entity - aggregate root for a knowledge vault."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from slugify import slugify


@dataclass
class Vault:
    """Vault entity representing a collection of documents.

    This is the aggregate root for a knowledge vault, containing
    documents, folders, tags, and their relationships.
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    description: str | None = None
    document_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Generate slug if not provided."""
        if self.name and not self.slug:
            self.slug = slugify(self.name, max_length=100)

    def update_name(self, name: str) -> None:
        """Update vault name and regenerate slug."""
        self.name = name
        self.slug = slugify(name, max_length=100)
        self._touch()

    def update_description(self, description: str | None) -> None:
        """Update vault description."""
        self.description = description
        self._touch()

    def increment_document_count(self, count: int = 1) -> None:
        """Increment document count."""
        self.document_count += count
        self._touch()

    def decrement_document_count(self, count: int = 1) -> None:
        """Decrement document count."""
        self.document_count = max(0, self.document_count - count)
        self._touch()

    def set_document_count(self, count: int) -> None:
        """Set document count to specific value."""
        self.document_count = max(0, count)
        self._touch()

    def _touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    @classmethod
    def create(
        cls,
        user_id: UUID,
        name: str,
        description: str | None = None,
    ) -> "Vault":
        """Factory method to create a new vault."""
        return cls(
            user_id=user_id,
            name=name,
            slug=slugify(name, max_length=100),
            description=description,
        )
