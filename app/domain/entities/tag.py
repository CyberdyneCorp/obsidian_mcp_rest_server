"""Tag entity representing a document tag."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.domain.services.slug import generate_slug


@dataclass
class Tag:
    """Tag entity representing a tag in the vault.

    Tags support hierarchy using "/" separator (e.g., #projects/ai/ml).
    The parent_tag_id references the parent in the hierarchy.
    """

    id: UUID = field(default_factory=uuid4)
    vault_id: UUID = field(default_factory=uuid4)
    name: str = ""  # Full tag name (e.g., "#projects/ai")
    slug: str = ""  # URL-safe version
    parent_tag_id: UUID | None = None
    document_count: int = 0

    def __post_init__(self) -> None:
        """Generate slug if not provided."""
        if self.name and not self.slug:
            # Remove # prefix if present
            clean_name = self.name.lstrip("#")
            self.slug = generate_slug(clean_name, separator="-")

    @property
    def is_hierarchical(self) -> bool:
        """Check if this tag has hierarchy (contains /)."""
        return "/" in self.name

    @property
    def parent_name(self) -> str | None:
        """Get parent tag name."""
        clean_name = self.name.lstrip("#")
        if "/" not in clean_name:
            return None
        return "#" + clean_name.rsplit("/", 1)[0]

    @property
    def leaf_name(self) -> str:
        """Get the leaf (last part) of the tag name."""
        clean_name = self.name.lstrip("#")
        if "/" not in clean_name:
            return clean_name
        return clean_name.rsplit("/", 1)[-1]

    @property
    def depth(self) -> int:
        """Get tag hierarchy depth (0 = root level)."""
        clean_name = self.name.lstrip("#")
        return clean_name.count("/")

    def increment_document_count(self, count: int = 1) -> None:
        """Increment document count."""
        self.document_count += count

    def decrement_document_count(self, count: int = 1) -> None:
        """Decrement document count."""
        self.document_count = max(0, self.document_count - count)

    @classmethod
    def create(
        cls,
        vault_id: UUID,
        name: str,
        parent: "Tag | None" = None,
    ) -> "Tag":
        """Factory method to create a new tag."""
        # Ensure name starts with #
        if not name.startswith("#"):
            name = "#" + name

        return cls(
            vault_id=vault_id,
            name=name,
            parent_tag_id=parent.id if parent else None,
        )

    @classmethod
    def parse_hierarchy(cls, tag_name: str) -> list[str]:
        """Parse a hierarchical tag into all parent tags.

        Example: "#projects/ai/ml" -> ["#projects", "#projects/ai", "#projects/ai/ml"]
        """
        clean_name = tag_name.lstrip("#")
        parts = clean_name.split("/")

        result = []
        current = ""
        for part in parts:
            current = f"{current}/{part}" if current else part
            result.append(f"#{current}")

        return result
