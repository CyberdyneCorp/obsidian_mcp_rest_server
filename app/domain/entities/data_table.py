"""DataTable entity representing a user-defined table."""

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.domain.value_objects.column_type import ColumnDefinition, TableSchema


def _utcnow_naive() -> datetime:
    """Return UTC timestamp as naive datetime for TIMESTAMP WITHOUT TIME ZONE."""
    return datetime.now(UTC).replace(tzinfo=None)


def _generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a name."""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:100]  # Limit to 100 chars


@dataclass
class DataTable:
    """Entity representing a user-defined data table.

    Tables have a schema (column definitions) and contain rows of data.
    They belong to a vault and can have relationships to other tables.
    """

    id: UUID = field(default_factory=uuid4)
    vault_id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    description: str | None = None
    schema: TableSchema = field(default_factory=TableSchema)
    row_count: int = 0
    created_at: datetime = field(default_factory=_utcnow_naive)
    updated_at: datetime = field(default_factory=_utcnow_naive)

    def __post_init__(self) -> None:
        """Initialize computed fields."""
        if self.name and not self.slug:
            self.slug = _generate_slug(self.name)

    @classmethod
    def create(
        cls,
        vault_id: UUID,
        name: str,
        columns: list[dict[str, Any]] | None = None,
        description: str | None = None,
        slug: str | None = None,
    ) -> "DataTable":
        """Factory method to create a new table.

        Args:
            vault_id: The vault this table belongs to
            name: Display name of the table
            columns: List of column definitions as dictionaries
            description: Optional description
            slug: Optional custom slug (auto-generated from name if not provided)
        """
        schema = TableSchema.from_list(columns or [])
        table_slug = slug if slug else _generate_slug(name)

        return cls(
            vault_id=vault_id,
            name=name,
            slug=table_slug,
            description=description,
            schema=schema,
            row_count=0,
        )

    def update_name(self, name: str) -> None:
        """Update the table name."""
        self.name = name
        self._touch()

    def update_description(self, description: str | None) -> None:
        """Update the table description."""
        self.description = description
        self._touch()

    def update_schema(self, schema: TableSchema) -> None:
        """Update the table schema."""
        self.schema = schema
        self._touch()

    def add_column(self, column: ColumnDefinition) -> None:
        """Add a new column to the schema."""
        self.schema = self.schema.add_column(column)
        self._touch()

    def remove_column(self, column_name: str) -> None:
        """Remove a column from the schema."""
        self.schema = self.schema.remove_column(column_name)
        self._touch()

    def increment_row_count(self, count: int = 1) -> None:
        """Increment the row count."""
        self.row_count += count
        self._touch()

    def decrement_row_count(self, count: int = 1) -> None:
        """Decrement the row count."""
        self.row_count = max(0, self.row_count - count)
        self._touch()

    def set_row_count(self, count: int) -> None:
        """Set the row count directly."""
        self.row_count = count
        self._touch()

    def _touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = _utcnow_naive()

    def validate_row_data(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate row data against the table schema.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        return self.schema.validate_row_data(data)

    @property
    def column_names(self) -> list[str]:
        """Get list of column names."""
        return self.schema.column_names

    @property
    def columns(self) -> tuple[ColumnDefinition, ...]:
        """Get column definitions."""
        return self.schema.columns

    def get_column(self, name: str) -> ColumnDefinition | None:
        """Get a column definition by name."""
        return self.schema.get_column(name)

    def has_column(self, name: str) -> bool:
        """Check if a column exists."""
        return self.schema.has_column(name)
