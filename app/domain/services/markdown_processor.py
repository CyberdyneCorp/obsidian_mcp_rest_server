"""MarkdownProcessor service for parsing Markdown documents."""

import re
from dataclasses import dataclass

from app.domain.value_objects.frontmatter import Frontmatter
from app.domain.value_objects.wiki_link import WikiLink


@dataclass
class ParsedDocument:
    """Result of parsing a Markdown document."""

    frontmatter: Frontmatter
    content: str  # Content without frontmatter
    links: list[WikiLink]
    tags: list[str]
    word_count: int


class MarkdownProcessor:
    """Service for processing Markdown documents.

    Handles:
    - Frontmatter extraction
    - Wiki-link extraction
    - Tag extraction
    - Word counting
    """

    # Frontmatter pattern: --- at start, YAML, ---
    _FRONTMATTER_PATTERN = re.compile(
        r"^---\s*\n(.*?)\n---\s*\n?",
        re.DOTALL,
    )

    # Wiki-link patterns (both standard and embed)
    _WIKILINK_PATTERN = re.compile(
        r"(!?\[\[)"  # Opening [[ or ![[
        r"([^\]]+)"  # Content
        r"\]\]",  # Closing ]]
    )

    # Inline tag pattern
    _TAG_PATTERN = re.compile(r"(?<!\S)#([a-zA-Z][a-zA-Z0-9_/]*)")

    def extract_frontmatter(self, content: str) -> tuple[Frontmatter, str]:
        """Separate frontmatter from content.

        Args:
            content: Full document content (may include frontmatter)

        Returns:
            Tuple of (Frontmatter, body_content)
        """
        match = self._FRONTMATTER_PATTERN.match(content)

        if match:
            yaml_text = match.group(1)
            body = content[match.end() :]
            frontmatter = Frontmatter.parse(yaml_text)
            return frontmatter, body.strip()

        return Frontmatter(), content.strip()

    def extract_links(self, content: str) -> list[WikiLink]:
        """Extract all wiki-links from content.

        Args:
            content: Markdown content

        Returns:
            List of WikiLink objects
        """
        links = []

        for match in self._WIKILINK_PATTERN.finditer(content):
            full_match = match.group(0)
            try:
                wiki_link = WikiLink.parse(full_match)
                links.append(wiki_link)
            except Exception:
                # Skip invalid links
                continue

        return links

    def extract_links_with_positions(
        self,
        content: str,
    ) -> list[tuple[WikiLink, int]]:
        """Extract wiki-links with their positions in the content.

        Args:
            content: Markdown content

        Returns:
            List of (WikiLink, position) tuples
        """
        links = []

        for match in self._WIKILINK_PATTERN.finditer(content):
            full_match = match.group(0)
            position = match.start()
            try:
                wiki_link = WikiLink.parse(full_match)
                links.append((wiki_link, position))
            except Exception:
                continue

        return links

    def extract_tags(self, content: str) -> list[str]:
        """Extract inline tags from content.

        Args:
            content: Markdown content

        Returns:
            List of tags (with # prefix)
        """
        matches = self._TAG_PATTERN.findall(content)
        seen = set()
        tags = []
        for match in matches:
            tag = f"#{match}"
            if tag not in seen:
                seen.add(tag)
                tags.append(tag)
        return tags

    def count_words(self, content: str) -> int:
        """Count words in Markdown content.

        Excludes:
        - Frontmatter
        - Code blocks
        - Links (counted as single words)
        - HTML tags

        Args:
            content: Markdown content (body only, no frontmatter)

        Returns:
            Word count
        """
        text = content

        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", " ", text)
        text = re.sub(r"`[^`]+`", " ", text)

        # Remove wiki-links but keep display text
        text = re.sub(r"!?\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
        text = re.sub(r"!?\[\[([^\]]+)\]\]", r"\1", text)

        # Remove standard markdown links
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

        # Remove markdown formatting
        text = re.sub(r"[#*_~`>]", " ", text)

        # Split and count
        words = text.split()
        return len(words)

    def parse(self, content: str) -> ParsedDocument:
        """Parse a complete Markdown document.

        Args:
            content: Full document content

        Returns:
            ParsedDocument with all extracted data
        """
        frontmatter, body = self.extract_frontmatter(content)
        links = self.extract_links(body)
        inline_tags = self.extract_tags(body)

        # Merge frontmatter tags with inline tags
        all_tags = list(frontmatter.tags) + inline_tags
        unique_tags = list(dict.fromkeys(all_tags))  # Preserve order, remove dupes

        word_count = self.count_words(body)

        return ParsedDocument(
            frontmatter=frontmatter,
            content=body,
            links=links,
            tags=unique_tags,
            word_count=word_count,
        )

    def render_with_frontmatter(
        self,
        content: str,
        frontmatter: Frontmatter,
    ) -> str:
        """Render content with frontmatter.

        Args:
            content: Body content
            frontmatter: Frontmatter to include

        Returns:
            Full Markdown document
        """
        yaml_text = frontmatter.to_yaml()

        if yaml_text:
            return f"---\n{yaml_text}---\n\n{content}"

        return content

    def get_heading(self, content: str) -> str | None:
        """Extract the first heading from content.

        Args:
            content: Markdown content

        Returns:
            First heading text or None
        """
        # Try H1 first
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Try H2
        match = re.search(r"^##\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        return None

    def get_excerpt(self, content: str, max_length: int = 200) -> str:
        """Get a text excerpt from content.

        Args:
            content: Markdown content
            max_length: Maximum excerpt length

        Returns:
            Plain text excerpt
        """
        # Remove frontmatter if present
        _, body = self.extract_frontmatter(content)

        # Remove headings
        text = re.sub(r"^#{1,6}\s+.*$", "", body, flags=re.MULTILINE)

        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"`[^`]+`", "", text)

        # Remove links but keep text
        text = re.sub(r"!?\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
        text = re.sub(r"!?\[\[([^\]]+)\]\]", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # Remove formatting
        text = re.sub(r"[*_~]", "", text)

        # Clean whitespace
        text = " ".join(text.split())

        if len(text) <= max_length:
            return text

        # Truncate at word boundary
        truncated = text[:max_length]
        last_space = truncated.rfind(" ")
        if last_space > max_length // 2:
            truncated = truncated[:last_space]

        return truncated + "..."
