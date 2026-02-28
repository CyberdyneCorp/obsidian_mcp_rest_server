"""PostgreSQL table row repository implementation."""

from typing import Any
from uuid import UUID

from sqlalchemy import func, select, and_, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.table_row import TableRow
from app.infrastructure.database.models.table_row import TableRowModel


class PostgresRowRepository:
    """PostgreSQL implementation of RowRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, row_id: UUID) -> TableRow | None:
        """Get row by ID."""
        stmt = select(TableRowModel).where(TableRowModel.id == row_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, row: TableRow) -> TableRow:
        """Create a new row."""
        model = self._to_model(row)
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def create_many(self, rows: list[TableRow]) -> list[TableRow]:
        """Create multiple rows."""
        models = [self._to_model(r) for r in rows]
        self.session.add_all(models)
        await self.session.flush()
        return [self._to_entity(m) for m in models]

    async def update(self, row: TableRow) -> TableRow:
        """Update an existing row."""
        stmt = select(TableRowModel).where(TableRowModel.id == row.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.data = row.data
            model.updated_at = row.updated_at
            await self.session.flush()
            return self._to_entity(model)

        return row

    async def delete(self, row_id: UUID) -> None:
        """Delete a row."""
        stmt = select(TableRowModel).where(TableRowModel.id == row_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def delete_by_table(self, table_id: UUID) -> int:
        """Delete all rows in a table. Returns count deleted."""
        stmt = select(TableRowModel).where(TableRowModel.table_id == table_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        count = len(models)
        for model in models:
            await self.session.delete(model)
        await self.session.flush()
        return count

    async def list_by_table(
        self,
        table_id: UUID,
        limit: int = 100,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
        sort_column: str | None = None,
        sort_order: str = "asc",
    ) -> list[TableRow]:
        """List rows in a table with filtering and pagination.

        Args:
            table_id: The table to list rows from
            limit: Maximum number of rows to return
            offset: Number of rows to skip
            filters: Dictionary of column -> value/operator filters
            sort_column: Column to sort by (from JSONB data)
            sort_order: 'asc' or 'desc'
        """
        stmt = select(TableRowModel).where(TableRowModel.table_id == table_id)

        # Apply filters
        if filters:
            filter_conditions = self._build_filter_conditions(filters)
            if filter_conditions:
                stmt = stmt.where(and_(*filter_conditions))

        # Apply sorting
        if sort_column:
            # Sort by JSONB field
            json_path = TableRowModel.data[sort_column].astext
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(json_path.desc())
            else:
                stmt = stmt.order_by(json_path.asc())
        else:
            stmt = stmt.order_by(TableRowModel.created_at.desc())

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def count_by_table(
        self,
        table_id: UUID,
        filters: dict[str, Any] | None = None,
    ) -> int:
        """Count rows in a table with optional filtering."""
        stmt = (
            select(func.count())
            .select_from(TableRowModel)
            .where(TableRowModel.table_id == table_id)
        )

        if filters:
            filter_conditions = self._build_filter_conditions(filters)
            if filter_conditions:
                stmt = stmt.where(and_(*filter_conditions))

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def search_fulltext(
        self,
        table_id: UUID,
        query: str,
        limit: int = 20,
    ) -> list[TableRow]:
        """Full-text search across all text fields in rows."""
        # Search in JSONB data - cast to text and use ILIKE
        stmt = (
            select(TableRowModel)
            .where(
                TableRowModel.table_id == table_id,
                cast(TableRowModel.data, String).ilike(f"%{query}%"),
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_by_field_value(
        self,
        table_id: UUID,
        field_name: str,
        value: Any,
    ) -> list[TableRow]:
        """Get rows where a specific field has a specific value."""
        stmt = select(TableRowModel).where(
            TableRowModel.table_id == table_id,
            TableRowModel.data[field_name].astext == str(value),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_referencing_rows(
        self,
        table_id: UUID,
        column_name: str,
        target_row_id: UUID,
    ) -> list[TableRow]:
        """Get rows that reference a specific row via a reference column."""
        stmt = select(TableRowModel).where(
            TableRowModel.table_id == table_id,
            TableRowModel.data[column_name].astext == str(target_row_id),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    def _build_filter_conditions(self, filters: dict[str, Any]) -> list:
        """Build SQLAlchemy filter conditions from a filter dictionary.

        Supports:
        - Simple equality: {"column": "value"}
        - Operators: {"column": {"gt": 10, "lt": 20}}
        - LIKE: {"column": {"like": "%pattern%"}}
        """
        conditions = []

        for key, value in filters.items():
            if isinstance(value, dict):
                # Operator-based filter
                for op, op_value in value.items():
                    json_field = TableRowModel.data[key].astext
                    if op == "eq":
                        conditions.append(json_field == str(op_value))
                    elif op == "ne":
                        conditions.append(json_field != str(op_value))
                    elif op == "gt":
                        conditions.append(json_field > str(op_value))
                    elif op == "gte":
                        conditions.append(json_field >= str(op_value))
                    elif op == "lt":
                        conditions.append(json_field < str(op_value))
                    elif op == "lte":
                        conditions.append(json_field <= str(op_value))
                    elif op == "like":
                        conditions.append(json_field.ilike(str(op_value)))
                    elif op == "in":
                        if isinstance(op_value, list):
                            conditions.append(
                                json_field.in_([str(v) for v in op_value])
                            )
            else:
                # Simple equality
                json_field = TableRowModel.data[key].astext
                conditions.append(json_field == str(value))

        return conditions

    def _to_entity(self, model: TableRowModel) -> TableRow:
        """Convert model to entity."""
        return TableRow(
            id=model.id,
            table_id=model.table_id,
            vault_id=model.vault_id,
            data=model.data or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: TableRow) -> TableRowModel:
        """Convert entity to model."""
        return TableRowModel(
            id=entity.id,
            table_id=entity.table_id,
            vault_id=entity.vault_id,
            data=entity.data,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
