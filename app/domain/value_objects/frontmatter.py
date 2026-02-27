"""Frontmatter value object for YAML document metadata."""

from dataclasses import dataclass, field
from typing import Any, Self

import yaml

from app.domain.exceptions import InvalidFrontmatterError


@dataclass(frozen=True)
class Frontmatter:
    """Value object representing YAML frontmatter metadata.

    Frontmatter is the YAML block at the start of a Markdown file:
    ---
    title: My Document
    aliases: [Doc, MyDoc]
    tags: [ai, ml]
    custom_field: value
    ---
    """

    title: str | None = None
    aliases: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    custom_fields: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def parse(cls, yaml_text: str) -> Self:
        """Parse YAML frontmatter text into Frontmatter object.

        Args:
            yaml_text: The YAML text (without --- delimiters)

        Returns:
            Frontmatter object

        Raises:
            InvalidFrontmatterError: If YAML is invalid
        """
        if not yaml_text.strip():
            return cls()

        try:
            data = yaml.safe_load(yaml_text)
        except yaml.YAMLError as e:
            raise InvalidFrontmatterError(str(e)) from e

        if not isinstance(data, dict):
            raise InvalidFrontmatterError("Frontmatter must be a YAML mapping")

        # Extract standard fields
        title = data.pop("title", None)
        if title is not None:
            title = str(title)

        # Handle aliases (can be string or list)
        aliases_raw = data.pop("aliases", [])
        if isinstance(aliases_raw, str):
            aliases = (aliases_raw,)
        elif isinstance(aliases_raw, list):
            aliases = tuple(str(a) for a in aliases_raw)
        else:
            aliases = ()

        # Handle tags (can be string or list)
        tags_raw = data.pop("tags", [])
        if isinstance(tags_raw, str):
            tags = (tags_raw,)
        elif isinstance(tags_raw, list):
            tags = tuple(str(t) for t in tags_raw)
        else:
            tags = ()

        # Remaining fields are custom
        custom_fields = dict(data)

        return cls(
            title=title,
            aliases=aliases,
            tags=tags,
            custom_fields=custom_fields,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create Frontmatter from a dictionary."""
        if not data:
            return cls()

        title = data.get("title")
        if title is not None:
            title = str(title)

        aliases_raw = data.get("aliases", [])
        if isinstance(aliases_raw, str):
            aliases = (aliases_raw,)
        elif isinstance(aliases_raw, (list, tuple)):
            aliases = tuple(str(a) for a in aliases_raw)
        else:
            aliases = ()

        tags_raw = data.get("tags", [])
        if isinstance(tags_raw, str):
            tags = (tags_raw,)
        elif isinstance(tags_raw, (list, tuple)):
            tags = tuple(str(t) for t in tags_raw)
        else:
            tags = ()

        # Get custom fields (everything except standard fields)
        standard_fields = {"title", "aliases", "tags"}
        custom_fields = {k: v for k, v in data.items() if k not in standard_fields}

        return cls(
            title=title,
            aliases=aliases,
            tags=tags,
            custom_fields=custom_fields,
        )

    def to_yaml(self) -> str:
        """Convert Frontmatter to YAML string."""
        data: dict[str, Any] = {}

        if self.title:
            data["title"] = self.title
        if self.aliases:
            data["aliases"] = list(self.aliases)
        if self.tags:
            data["tags"] = list(self.tags)

        data.update(self.custom_fields)

        if not data:
            return ""

        return yaml.safe_dump(data, default_flow_style=False, allow_unicode=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert Frontmatter to dictionary."""
        data: dict[str, Any] = {}

        if self.title:
            data["title"] = self.title
        if self.aliases:
            data["aliases"] = list(self.aliases)
        if self.tags:
            data["tags"] = list(self.tags)

        data.update(self.custom_fields)

        return data

    def with_title(self, title: str) -> Self:
        """Return new Frontmatter with updated title."""
        return type(self)(
            title=title,
            aliases=self.aliases,
            tags=self.tags,
            custom_fields=self.custom_fields,
        )

    def with_tags(self, tags: tuple[str, ...]) -> Self:
        """Return new Frontmatter with updated tags."""
        return type(self)(
            title=self.title,
            aliases=self.aliases,
            tags=tags,
            custom_fields=self.custom_fields,
        )

    def merge(self, other: "Frontmatter") -> Self:
        """Merge another Frontmatter into this one.

        The other Frontmatter's values take precedence.
        """
        merged_custom = {**self.custom_fields, **other.custom_fields}

        return type(self)(
            title=other.title or self.title,
            aliases=tuple(set(self.aliases + other.aliases)),
            tags=tuple(set(self.tags + other.tags)),
            custom_fields=merged_custom,
        )
