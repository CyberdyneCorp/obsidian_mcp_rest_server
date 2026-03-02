"""Document entity representing a Markdown document."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID, uuid4

from app.domain.value_objects.frontmatter import Frontmatter


def _utcnow_naive() -> datetime:
    """Return UTC timestamp as naive datetime for TIMESTAMP WITHOUT TIME ZONE."""
    return datetime.now(UTC).replace(tzinfo=None)


@dataclass
class Document:
    """Document entity representing a Markdown document in the vault.

    Documents contain the content, metadata (frontmatter), and
    maintain counts of links and backlinks.
    """

    id: UUID = field(default_factory=uuid4)
    vault_id: UUID = field(default_factory=uuid4)
    folder_id: UUID | None = None
    title: str = ""
    filename: str = ""
    path: str = ""
    content: str = ""
    content_hash: str = ""
    frontmatter: Frontmatter = field(default_factory=Frontmatter)
    aliases: list[str] = field(default_factory=list)
    word_count: int = 0
    link_count: int = 0
    backlink_count: int = 0
    created_at: datetime = field(default_factory=_utcnow_naive)
    updated_at: datetime = field(default_factory=_utcnow_naive)

    def __post_init__(self) -> None:
        """Initialize computed fields."""
        if self.content and not self.content_hash:
            self.content_hash = self._compute_hash(self.content)
        if self.content and self.word_count == 0:
            self.word_count = self._count_words(self.content)
        if self.path and not self.filename:
            self.filename = self.path.split("/")[-1]
        if self.path and not self.title:
            self.title = self._extract_title_from_path(self.path)
        # Merge aliases from frontmatter
        if self.frontmatter and self.frontmatter.aliases:
            self.aliases = list(set(self.aliases + list(self.frontmatter.aliases)))

    @staticmethod
    def _compute_hash(content: str) -> str:
        """Compute SHA-256 hash of content."""
        return sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _count_words(content: str) -> int:
        """Count words in content (simple split)."""
        return len(content.split())

    @staticmethod
    def _extract_title_from_path(path: str) -> str:
        """Extract title from file path (filename without extension)."""
        filename = path.split("/")[-1]
        if filename.endswith(".md"):
            return filename[:-3]
        return filename

    def update_content(self, content: str) -> None:
        """Update document content and recompute hash/word count."""
        self.content = content
        self.content_hash = self._compute_hash(content)
        self.word_count = self._count_words(content)
        self._touch()

    def update_frontmatter(self, frontmatter: Frontmatter) -> None:
        """Update document frontmatter."""
        self.frontmatter = frontmatter
        if frontmatter.title:
            self.title = frontmatter.title
        if frontmatter.aliases:
            self.aliases = list(set(self.aliases + list(frontmatter.aliases)))
        self._touch()

    def set_link_count(self, count: int) -> None:
        """Set the outgoing link count."""
        self.link_count = count
        self._touch()

    def set_backlink_count(self, count: int) -> None:
        """Set the incoming backlink count."""
        self.backlink_count = count
        self._touch()

    def increment_backlink_count(self, count: int = 1) -> None:
        """Increment backlink count."""
        self.backlink_count += count

    def decrement_backlink_count(self, count: int = 1) -> None:
        """Decrement backlink count."""
        self.backlink_count = max(0, self.backlink_count - count)

    def _touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = _utcnow_naive()

    def has_changed(self, new_content: str) -> bool:
        """Check if content has changed by comparing hashes."""
        new_hash = self._compute_hash(new_content)
        return new_hash != self.content_hash

    @property
    def folder_path(self) -> str | None:
        """Get the folder path (path without filename)."""
        if "/" not in self.path:
            return None
        return self.path.rsplit("/", 1)[0]

    @classmethod
    def create(
        cls,
        vault_id: UUID,
        path: str,
        content: str,
        frontmatter: Frontmatter | None = None,
        folder_id: UUID | None = None,
    ) -> "Document":
        """Factory method to create a new document."""
        fm = frontmatter or Frontmatter()

        # Extract title from frontmatter or path
        title = fm.title or cls._extract_title_from_path(path)

        return cls(
            vault_id=vault_id,
            folder_id=folder_id,
            title=title,
            filename=path.split("/")[-1],
            path=path,
            content=content,
            content_hash=cls._compute_hash(content),
            frontmatter=fm,
            aliases=list(fm.aliases) if fm.aliases else [],
            word_count=cls._count_words(content),
        )
