"""Domain-level repository port interfaces.

These are the minimal interfaces that domain services depend on.
They define the contract for persistence without any infrastructure details.
"""

from typing import Protocol
from uuid import UUID

from app.domain.entities.data_table import DataTable
from app.domain.entities.table_relationship import TableRelationship
from app.domain.entities.table_row import TableRow


class TableRepositoryPort(Protocol):
    """Domain port for table persistence operations needed by domain services."""

    async def get_by_id(self, table_id: UUID) -> DataTable | None:
        """Get table by ID."""
        ...

    async def increment_row_count(self, table_id: UUID, delta: int = 1) -> None:
        """Increment the row count for a table."""
        ...


class RowRepositoryPort(Protocol):
    """Domain port for row persistence operations needed by domain services."""

    async def get_by_id(self, row_id: UUID) -> TableRow | None:
        """Get row by ID."""
        ...

    async def update(self, row: TableRow) -> TableRow:
        """Update an existing row."""
        ...

    async def delete(self, row_id: UUID) -> bool:
        """Delete a row."""
        ...

    async def get_referencing_rows(
        self,
        table_id: UUID,
        column_name: str,
        target_row_id: UUID,
    ) -> list[TableRow]:
        """Get rows that reference a specific row via a reference column."""
        ...


class RelationshipRepositoryPort(Protocol):
    """Domain port for relationship persistence operations needed by domain services."""

    async def get_by_source_table(
        self, source_table_id: UUID
    ) -> list[TableRelationship]:
        """Get all relationships where the given table is the source."""
        ...

    async def get_by_target_table(
        self, target_table_id: UUID
    ) -> list[TableRelationship]:
        """Get all relationships where the given table is the target."""
        ...

    async def get_restrict_relationships(
        self, target_table_id: UUID
    ) -> list[TableRelationship]:
        """Get relationships with RESTRICT delete for a target table."""
        ...
