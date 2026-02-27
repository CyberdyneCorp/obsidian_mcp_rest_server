"""Folder entity representing a folder in the vault hierarchy."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Folder:
    """Folder entity representing a directory in the vault.

    Folders form a tree structure with parent-child relationships.
    The path is the full path from root (e.g., "Projects/AI/ML").
    """

    id: UUID = field(default_factory=uuid4)
    vault_id: UUID = field(default_factory=uuid4)
    parent_id: UUID | None = None
    name: str = ""
    path: str = ""
    depth: int = 0

    def __post_init__(self) -> None:
        """Calculate depth from path if not provided."""
        if self.path and self.depth == 0:
            self.depth = self.path.count("/")

    @property
    def is_root(self) -> bool:
        """Check if this is a root folder (no parent)."""
        return self.parent_id is None

    @property
    def parent_path(self) -> str | None:
        """Get parent folder path."""
        if "/" not in self.path:
            return None
        return self.path.rsplit("/", 1)[0]

    @classmethod
    def create(
        cls,
        vault_id: UUID,
        name: str,
        parent: "Folder | None" = None,
    ) -> "Folder":
        """Factory method to create a new folder."""
        if parent:
            path = f"{parent.path}/{name}"
            depth = parent.depth + 1
            parent_id = parent.id
        else:
            path = name
            depth = 0
            parent_id = None

        return cls(
            vault_id=vault_id,
            parent_id=parent_id,
            name=name,
            path=path,
            depth=depth,
        )

    @classmethod
    def from_path(cls, vault_id: UUID, path: str) -> "Folder":
        """Create folder from full path."""
        parts = path.split("/")
        name = parts[-1]
        depth = len(parts) - 1

        return cls(
            vault_id=vault_id,
            name=name,
            path=path,
            depth=depth,
        )
