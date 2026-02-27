"""DocumentPath value object for file paths within a vault."""

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class DocumentPath:
    """Value object representing a document path within a vault.

    Handles path operations like extracting folder path, filename,
    and title from the full path.

    Example: "Projects/AI/Machine Learning.md"
    - folder_path: "Projects/AI"
    - filename: "Machine Learning.md"
    - title: "Machine Learning"
    """

    path: str

    def __post_init__(self) -> None:
        """Validate and normalize the path."""
        # Use object.__setattr__ for frozen dataclass
        normalized = self._normalize(self.path)
        object.__setattr__(self, "path", normalized)

    @staticmethod
    def _normalize(path: str) -> str:
        """Normalize the path."""
        # Remove leading/trailing slashes and whitespace
        path = path.strip().strip("/")

        # Collapse multiple slashes
        while "//" in path:
            path = path.replace("//", "/")

        return path

    @property
    def folder_path(self) -> str | None:
        """Get the folder path (path without filename).

        Returns None if the document is at the root level.
        """
        if "/" not in self.path:
            return None
        return self.path.rsplit("/", 1)[0]

    @property
    def filename(self) -> str:
        """Get the filename including extension."""
        return self.path.split("/")[-1]

    @property
    def title(self) -> str:
        """Get the title (filename without .md extension)."""
        filename = self.filename
        if filename.lower().endswith(".md"):
            return filename[:-3]
        return filename

    @property
    def extension(self) -> str | None:
        """Get the file extension (without dot)."""
        if "." not in self.filename:
            return None
        return self.filename.rsplit(".", 1)[-1].lower()

    @property
    def is_markdown(self) -> bool:
        """Check if this is a Markdown file."""
        return self.extension == "md"

    @property
    def depth(self) -> int:
        """Get the depth of the path (number of folders)."""
        return self.path.count("/")

    @property
    def parts(self) -> tuple[str, ...]:
        """Get all path parts."""
        return tuple(self.path.split("/"))

    @property
    def folder_parts(self) -> tuple[str, ...]:
        """Get folder parts (excluding filename)."""
        parts = self.path.split("/")
        return tuple(parts[:-1]) if len(parts) > 1 else ()

    def with_extension(self, ext: str) -> Self:
        """Return new path with different extension."""
        if not ext.startswith("."):
            ext = "." + ext

        if self.extension:
            new_filename = self.filename.rsplit(".", 1)[0] + ext
        else:
            new_filename = self.filename + ext

        if self.folder_path:
            new_path = f"{self.folder_path}/{new_filename}"
        else:
            new_path = new_filename

        return type(self)(new_path)

    def in_folder(self, folder: str) -> Self:
        """Return new path in a different folder."""
        folder = folder.strip("/")
        if folder:
            return type(self)(f"{folder}/{self.filename}")
        return type(self)(self.filename)

    def is_under(self, folder_path: str) -> bool:
        """Check if this path is under the given folder."""
        folder_path = folder_path.strip("/")
        if not folder_path:
            return True
        return self.path.startswith(folder_path + "/")

    def relative_to(self, base_folder: str) -> Self:
        """Get path relative to a base folder."""
        base_folder = base_folder.strip("/")
        if not base_folder:
            return self

        if not self.is_under(base_folder):
            return self

        relative = self.path[len(base_folder) + 1 :]
        return type(self)(relative)

    @classmethod
    def join(cls, *parts: str) -> Self:
        """Join path parts into a DocumentPath."""
        cleaned = [p.strip("/") for p in parts if p.strip("/")]
        return cls("/".join(cleaned))

    def __str__(self) -> str:
        return self.path

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DocumentPath):
            return self.path.lower() == other.path.lower()
        if isinstance(other, str):
            return self.path.lower() == other.lower().strip("/")
        return False

    def __hash__(self) -> int:
        return hash(self.path.lower())
