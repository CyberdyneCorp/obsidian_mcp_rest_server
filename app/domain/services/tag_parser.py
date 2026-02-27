"""TagParser service for extracting and parsing tags."""

import re


class TagParser:
    """Service for extracting and parsing tags from content.

    Supports:
    - Inline tags: #tag, #tag/subtag
    - Frontmatter tags: tags: [tag1, tag2]
    - Hierarchical tags with / separator
    """

    # Pattern for inline tags
    # Must start with # followed by letter, then alphanumeric, underscore, or /
    # Negative lookbehind to avoid matching inside words
    _TAG_PATTERN = re.compile(r"(?<!\S)#([a-zA-Z][a-zA-Z0-9_/]*)")

    def extract_inline_tags(self, content: str) -> list[str]:
        """Extract inline tags from content.

        Args:
            content: Markdown content

        Returns:
            List of tags (with # prefix)
        """
        matches = self._TAG_PATTERN.findall(content)
        # Add # prefix back and deduplicate while preserving order
        seen = set()
        tags = []
        for match in matches:
            tag = f"#{match}"
            if tag not in seen:
                seen.add(tag)
                tags.append(tag)
        return tags

    def parse_hierarchical_tag(self, tag: str) -> list[str]:
        """Parse a hierarchical tag into all parent tags.

        Example: "#projects/ai/ml" -> ["#projects", "#projects/ai", "#projects/ai/ml"]

        Args:
            tag: Tag string (with or without # prefix)

        Returns:
            List of tags from root to leaf
        """
        clean_tag = tag.lstrip("#")
        parts = clean_tag.split("/")

        result = []
        current = ""
        for part in parts:
            if current:
                current = f"{current}/{part}"
            else:
                current = part
            result.append(f"#{current}")

        return result

    def normalize_tag(self, tag: str) -> str:
        """Normalize a tag for consistent storage.

        - Ensures # prefix
        - Lowercase
        - Removes extra whitespace

        Args:
            tag: Tag string

        Returns:
            Normalized tag
        """
        tag = tag.strip()
        if not tag.startswith("#"):
            tag = "#" + tag
        return tag.lower()

    def is_valid_tag(self, tag: str) -> bool:
        """Check if a tag is valid.

        Args:
            tag: Tag string to validate

        Returns:
            True if valid
        """
        clean_tag = tag.lstrip("#")

        # Must start with a letter
        if not clean_tag or not clean_tag[0].isalpha():
            return False

        # Check remaining characters
        for char in clean_tag:
            if not (char.isalnum() or char in "_/"):
                return False

        # No empty parts in hierarchy
        if "//" in clean_tag:
            return False

        # No trailing slash
        if clean_tag.endswith("/"):
            return False

        return True

    def get_tag_depth(self, tag: str) -> int:
        """Get the depth of a hierarchical tag.

        Args:
            tag: Tag string

        Returns:
            Depth (0 = root level)
        """
        clean_tag = tag.lstrip("#")
        return clean_tag.count("/")

    def get_parent_tag(self, tag: str) -> str | None:
        """Get the parent tag of a hierarchical tag.

        Args:
            tag: Tag string

        Returns:
            Parent tag or None if root level
        """
        clean_tag = tag.lstrip("#")
        if "/" not in clean_tag:
            return None
        return "#" + clean_tag.rsplit("/", 1)[0]

    def get_root_tag(self, tag: str) -> str:
        """Get the root tag of a hierarchical tag.

        Args:
            tag: Tag string

        Returns:
            Root tag (first part)
        """
        clean_tag = tag.lstrip("#")
        if "/" not in clean_tag:
            return f"#{clean_tag}"
        return "#" + clean_tag.split("/")[0]

    def merge_tags(
        self,
        frontmatter_tags: list[str],
        inline_tags: list[str],
    ) -> list[str]:
        """Merge frontmatter and inline tags, removing duplicates.

        Args:
            frontmatter_tags: Tags from frontmatter
            inline_tags: Tags from content

        Returns:
            Merged list of unique tags
        """
        # Normalize all tags
        all_tags = set()

        for tag in frontmatter_tags:
            normalized = self.normalize_tag(tag)
            all_tags.add(normalized)

        for tag in inline_tags:
            normalized = self.normalize_tag(tag)
            all_tags.add(normalized)

        return sorted(all_tags)

    def expand_hierarchical_tags(self, tags: list[str]) -> list[str]:
        """Expand hierarchical tags to include all parent tags.

        Example: ["#projects/ai"] -> ["#projects", "#projects/ai"]

        Args:
            tags: List of tags

        Returns:
            Expanded list with all parent tags
        """
        expanded = set()

        for tag in tags:
            hierarchy = self.parse_hierarchical_tag(tag)
            expanded.update(hierarchy)

        return sorted(expanded)
