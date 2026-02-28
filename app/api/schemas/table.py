"""Table schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ColumnSchema(BaseModel):
    """Column definition schema."""

    name: str = Field(min_length=1, max_length=255)
    type: str = Field(
        description="Column type: text, number, boolean, date, datetime, json, array, reference, document, computed, richtext"
    )
    required: bool = False
    unique: bool = False
    default: Any = None
    description: str | None = None
    reference_table: str | None = Field(
        default=None,
        description="Required for 'reference' type - the target table slug",
    )
    reference_column: str = Field(
        default="id",
        description="Target column for reference (default: 'id')",
    )
    array_type: str | None = Field(
        default=None,
        description="Required for 'array' type - the element type",
    )
    formula: str | None = Field(
        default=None,
        description="Required for 'computed' type - the formula expression",
    )


class TableCreate(BaseModel):
    """Table creation request."""

    name: str = Field(min_length=1, max_length=255)
    columns: list[ColumnSchema] = Field(default_factory=list)
    description: str | None = None
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-safe identifier (auto-generated from name if not provided)",
    )


class TableUpdate(BaseModel):
    """Table update request."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    columns: list[ColumnSchema] | None = None


class ColumnResponse(BaseModel):
    """Column definition response."""

    name: str
    type: str
    required: bool
    unique: bool
    default: Any
    description: str | None
    reference_table: str | None
    reference_column: str
    array_type: str | None
    formula: str | None


class TableResponse(BaseModel):
    """Full table response."""

    id: UUID
    name: str
    slug: str
    description: str | None
    columns: list[ColumnResponse]
    row_count: int
    created_at: datetime
    updated_at: datetime


class TableSummaryResponse(BaseModel):
    """Table summary response."""

    id: UUID
    name: str
    slug: str
    description: str | None
    column_count: int
    row_count: int
    updated_at: datetime


class TableListResponse(BaseModel):
    """Table list response."""

    tables: list[TableSummaryResponse]
    total: int
    limit: int
    offset: int


# Row schemas
class RowCreate(BaseModel):
    """Row creation request."""

    data: dict[str, Any] = Field(default_factory=dict)


class RowUpdate(BaseModel):
    """Row update request."""

    data: dict[str, Any]


class RowResponse(BaseModel):
    """Row response."""

    id: UUID
    table_id: UUID
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class RowListResponse(BaseModel):
    """Row list response."""

    rows: list[RowResponse]
    total: int
    limit: int
    offset: int
