"""Table DTOs."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.entities.data_table import DataTable
from app.domain.entities.table_row import TableRow


@dataclass
class ColumnDTO:
    """Column definition DTO."""

    name: str
    type: str
    required: bool = False
    unique: bool = False
    default: Any = None
    description: str | None = None
    reference_table: str | None = None
    reference_column: str = "id"
    array_type: str | None = None
    formula: str | None = None


@dataclass
class TableDTO:
    """Table data transfer object."""

    id: UUID
    name: str
    slug: str
    description: str | None
    columns: list[ColumnDTO]
    row_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, table: DataTable) -> "TableDTO":
        """Create DTO from entity."""
        columns = [
            ColumnDTO(
                name=col.name,
                type=col.type.value,
                required=col.required,
                unique=col.unique,
                default=col.default,
                description=col.description,
                reference_table=col.reference_table,
                reference_column=col.reference_column,
                array_type=col.array_type.value if col.array_type else None,
                formula=col.formula,
            )
            for col in table.schema.columns
        ]
        return cls(
            id=table.id,
            name=table.name,
            slug=table.slug,
            description=table.description,
            columns=columns,
            row_count=table.row_count,
            created_at=table.created_at,
            updated_at=table.updated_at,
        )


@dataclass
class TableSummaryDTO:
    """Table summary DTO."""

    id: UUID
    name: str
    slug: str
    description: str | None
    column_count: int
    row_count: int
    updated_at: datetime

    @classmethod
    def from_entity(cls, table: DataTable) -> "TableSummaryDTO":
        """Create DTO from entity."""
        return cls(
            id=table.id,
            name=table.name,
            slug=table.slug,
            description=table.description,
            column_count=len(table.schema.columns),
            row_count=table.row_count,
            updated_at=table.updated_at,
        )


@dataclass
class TableCreateDTO:
    """DTO for creating a table."""

    name: str
    columns: list[dict[str, Any]]
    description: str | None = None
    slug: str | None = None


@dataclass
class TableUpdateDTO:
    """DTO for updating a table."""

    name: str | None = None
    description: str | None = None
    columns: list[dict[str, Any]] | None = None


@dataclass
class RowDTO:
    """Row data transfer object."""

    id: UUID
    table_id: UUID
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, row: TableRow) -> "RowDTO":
        """Create DTO from entity."""
        return cls(
            id=row.id,
            table_id=row.table_id,
            data=row.data,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


@dataclass
class RowCreateDTO:
    """DTO for creating a row."""

    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RowUpdateDTO:
    """DTO for updating a row."""

    data: dict[str, Any] | None = None
