"""DocumentTableLink entity representing a link between a document and a table/row."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class TableLinkType(str, Enum):
    """Type of link between document and table."""

    TABLE = "table"  # Link to entire table [[table:TableName]]
    TABLE_ROW = "table_row"  # Link to specific row [[row:TableName/uuid]]


@dataclass
class DocumentTableLink:
    """Entity representing a link from a document to a table or table row.

    These links are extracted from document content when parsing
    [[table:TableName]] or [[row:TableName/uuid]] syntax.
    """

    id: UUID = field(default_factory=uuid4)
    vault_id: UUID = field(default_factory=uuid4)
    document_id: UUID = field(default_factory=uuid4)
    table_id: UUID = field(default_factory=uuid4)
    row_id: UUID | None = None  # None means link is to whole table
    link_type: TableLinkType = TableLinkType.TABLE
    link_text: str = ""  # Original link text from document
    position_start: int | None = None  # Character position in document
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create_table_link(
        cls,
        vault_id: UUID,
        document_id: UUID,
        table_id: UUID,
        link_text: str,
        position_start: int | None = None,
    ) -> "DocumentTableLink":
        """Factory method to create a link to a table.

        Args:
            vault_id: The vault this link belongs to
            document_id: The source document containing the link
            table_id: The target table being linked to
            link_text: The original link text (e.g., "[[table:Contacts]]")
            position_start: Character position in document
        """
        return cls(
            vault_id=vault_id,
            document_id=document_id,
            table_id=table_id,
            row_id=None,
            link_type=TableLinkType.TABLE,
            link_text=link_text,
            position_start=position_start,
        )

    @classmethod
    def create_row_link(
        cls,
        vault_id: UUID,
        document_id: UUID,
        table_id: UUID,
        row_id: UUID,
        link_text: str,
        position_start: int | None = None,
    ) -> "DocumentTableLink":
        """Factory method to create a link to a specific row.

        Args:
            vault_id: The vault this link belongs to
            document_id: The source document containing the link
            table_id: The table containing the row
            row_id: The specific row being linked to
            link_text: The original link text (e.g., "[[row:Contacts/uuid]]")
            position_start: Character position in document
        """
        return cls(
            vault_id=vault_id,
            document_id=document_id,
            table_id=table_id,
            row_id=row_id,
            link_type=TableLinkType.TABLE_ROW,
            link_text=link_text,
            position_start=position_start,
        )

    @property
    def is_table_link(self) -> bool:
        """Check if this is a link to a whole table."""
        return self.link_type == TableLinkType.TABLE

    @property
    def is_row_link(self) -> bool:
        """Check if this is a link to a specific row."""
        return self.link_type == TableLinkType.TABLE_ROW
