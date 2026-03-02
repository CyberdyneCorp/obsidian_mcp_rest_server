"""WikiLink value object for parsing wiki-style links."""

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from app.domain.exceptions import InvalidWikiLinkError


class WikiLinkType(StrEnum):
    """Type of wiki link."""

    DOCUMENT = "document"  # Regular document link [[Target]]
    TABLE = "table"  # Table link [[table:TableName]]
    TABLE_ROW = "table_row"  # Row link [[row:TableName/uuid]]


@dataclass(frozen=True)
class WikiLink:
    """Value object representing a wiki-style link.

    Supports formats:
    - [[Target]] - Basic link
    - [[Target|Display]] - Link with custom display text
    - [[Target#Heading]] - Link to heading
    - [[Target#^block-id]] - Link to block
    - ![[Target]] - Embed (transclude)
    - [[table:TableName]] - Link to table
    - [[row:TableName/uuid]] - Link to specific row
    """

    target: str  # Target document name/path
    display_text: str  # Display text (same as target if not specified)
    heading: str | None = None  # Optional heading reference
    block_id: str | None = None  # Optional block ID reference
    is_embed: bool = False  # True if this is an embed (![[...]])
    link_type: WikiLinkType = WikiLinkType.DOCUMENT
    table_name: str | None = None  # For table/row links
    row_id: str | None = None  # For row links

    # Regex patterns for parsing
    # Embed: ![[target|display]]
    _EMBED_PATTERN = re.compile(
        r"^!\[\["
        r"([^\]#|]+)"  # target
        r"(?:#(?:\^([^\]|]+)|([^\]|]+)))?"  # optional #^block or #heading
        r"(?:\|([^\]]+))?"  # optional |display
        r"\]\]$"
    )

    # Standard link: [[target|display]]
    _LINK_PATTERN = re.compile(
        r"^\[\["
        r"([^\]#|]+)"  # target
        r"(?:#(?:\^([^\]|]+)|([^\]|]+)))?"  # optional #^block or #heading
        r"(?:\|([^\]]+))?"  # optional |display
        r"\]\]$"
    )

    # Table link: [[table:TableName]]
    _TABLE_LINK_PATTERN = re.compile(
        r"^\[\[table:([^\]|]+)(?:\|([^\]]+))?\]\]$"
    )

    # Row link: [[row:TableName/uuid]]
    _ROW_LINK_PATTERN = re.compile(
        r"^\[\[row:([^/\]]+)/([^\]|]+)(?:\|([^\]]+))?\]\]$"
    )

    @classmethod
    def parse(cls, text: str) -> Self:
        """Parse a wiki-link string into a WikiLink object.

        Args:
            text: The wiki-link text including brackets (e.g., "[[Target]]")

        Returns:
            WikiLink object

        Raises:
            InvalidWikiLinkError: If the text is not a valid wiki-link
        """
        text = text.strip()

        # Try table link pattern first
        match = cls._TABLE_LINK_PATTERN.match(text)
        if match:
            table_name = match.group(1).strip()
            display = match.group(2)

            return cls(
                target=f"table:{table_name}",
                display_text=display.strip() if display else table_name,
                link_type=WikiLinkType.TABLE,
                table_name=table_name,
            )

        # Try row link pattern
        match = cls._ROW_LINK_PATTERN.match(text)
        if match:
            table_name = match.group(1).strip()
            row_id = match.group(2).strip()
            display = match.group(3)

            return cls(
                target=f"row:{table_name}/{row_id}",
                display_text=display.strip() if display else f"{table_name}/{row_id}",
                link_type=WikiLinkType.TABLE_ROW,
                table_name=table_name,
                row_id=row_id,
            )

        # Try embed pattern
        match = cls._EMBED_PATTERN.match(text)
        if match:
            target = match.group(1).strip()
            block_id = match.group(2)
            heading = match.group(3)
            display = match.group(4)

            return cls(
                target=target,
                display_text=display.strip() if display else target,
                heading=heading.strip() if heading else None,
                block_id=block_id.strip() if block_id else None,
                is_embed=True,
                link_type=WikiLinkType.DOCUMENT,
            )

        # Try standard link pattern
        match = cls._LINK_PATTERN.match(text)
        if match:
            target = match.group(1).strip()
            block_id = match.group(2)
            heading = match.group(3)
            display = match.group(4)

            return cls(
                target=target,
                display_text=display.strip() if display else target,
                heading=heading.strip() if heading else None,
                block_id=block_id.strip() if block_id else None,
                is_embed=False,
                link_type=WikiLinkType.DOCUMENT,
            )

        raise InvalidWikiLinkError(text, "Does not match wiki-link pattern")

    @classmethod
    def is_valid(cls, text: str) -> bool:
        """Check if text is a valid wiki-link."""
        try:
            cls.parse(text)
            return True
        except InvalidWikiLinkError:
            return False

    def to_markdown(self) -> str:
        """Convert back to Markdown wiki-link syntax."""
        prefix = "!" if self.is_embed else ""
        suffix = ""

        if self.block_id:
            suffix = f"#^{self.block_id}"
        elif self.heading:
            suffix = f"#{self.heading}"

        if self.display_text != self.target:
            return f"{prefix}[[{self.target}{suffix}|{self.display_text}]]"
        return f"{prefix}[[{self.target}{suffix}]]"

    @property
    def is_heading_link(self) -> bool:
        """Check if this is a heading link."""
        return self.heading is not None

    @property
    def is_block_link(self) -> bool:
        """Check if this is a block reference link."""
        return self.block_id is not None

    @property
    def is_table_link(self) -> bool:
        """Check if this is a table link."""
        return self.link_type == WikiLinkType.TABLE

    @property
    def is_row_link(self) -> bool:
        """Check if this is a row link."""
        return self.link_type == WikiLinkType.TABLE_ROW

    @property
    def is_document_link(self) -> bool:
        """Check if this is a document link."""
        return self.link_type == WikiLinkType.DOCUMENT

    @property
    def full_target(self) -> str:
        """Get full target including heading/block."""
        if self.block_id:
            return f"{self.target}#^{self.block_id}"
        if self.heading:
            return f"{self.target}#{self.heading}"
        return self.target
