"""PostgreSQL table row repository implementation."""

from typing import Any
from uuid import UUID

from sqlalchemy import func, select, and_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.table_row import TableRow
from app.infrastructure.database.models.table_row import TableRowModel
from app.infrastructure.database.repositories.base import BaseRepository


class PostgresRowRepository(BaseRepository[TableRow, TableRowModel]):
    """PostgreSQL implementation of RowRepository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    def _get_model_class(self) -> type[TableRowModel]:
        return TableRowModel


    async def update(self, row: TableRow) -> TableRow:
        """Update an existing row."""
        model = await self._get_model_by_id(row.id)

        if model:
            model.data = row.data
            model.updated_at = row.updated_at
            await self.session.flush()
            self._logger.info(f"Updated row id={row.id}")
            return self._to_entity(model)

        self._logger.warning(f"Cannot update row: not found with id={row.id}")
        return row

    async def delete_by_table(self, table_id: UUID) -> int:
        """Delete all rows in a table. Returns count deleted."""
        return await self._delete_by_filter(TableRowModel.table_id == table_id)

    async def list_by_table(
        self,
        table_id: UUID,
        limit: int = 100,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
        sort_column: str | None = None,
        sort_order: str = "asc",
    ) -> list[TableRow]:
        """List rows in a table with filtering and pagination."""
        stmt = select(TableRowModel).where(TableRowModel.table_id == table_id)

        # Apply filters
        if filters:
            filter_conditions = self._build_filter_conditions(filters)
            if filter_conditions:
                stmt = stmt.where(and_(*filter_conditions))

        # Apply sorting
        if sort_column:
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
        self._logger.debug(f"Listed {len(models)} rows from table={table_id}")
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
        self._logger.debug(f"Fulltext search for '{query}' found {len(models)} rows")
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
        self._logger.debug(
            f"Found {len(models)} rows referencing {target_row_id} via {column_name}"
        )
        return [self._to_entity(m) for m in models]

    def _build_filter_conditions(self, filters: dict[str, Any]) -> list:
        """Build SQLAlchemy filter conditions from a filter dictionary."""
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
