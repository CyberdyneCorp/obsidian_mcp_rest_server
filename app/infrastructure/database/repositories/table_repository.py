"""PostgreSQL data table repository implementation."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.data_table import DataTable
from app.domain.value_objects.column_type import TableSchema
from app.infrastructure.database.models.data_table import DataTableModel


class PostgresTableRepository:
    """PostgreSQL implementation of TableRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, table_id: UUID) -> DataTable | None:
        """Get table by ID."""
        stmt = select(DataTableModel).where(DataTableModel.id == table_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_slug(self, vault_id: UUID, slug: str) -> DataTable | None:
        """Get table by vault ID and slug."""
        stmt = select(DataTableModel).where(
            DataTableModel.vault_id == vault_id,
            DataTableModel.slug == slug,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, table: DataTable) -> DataTable:
        """Create a new table."""
        model = self._to_model(table)
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def update(self, table: DataTable) -> DataTable:
        """Update an existing table."""
        stmt = select(DataTableModel).where(DataTableModel.id == table.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.name = table.name
            model.slug = table.slug
            model.description = table.description
            model.schema = table.schema.to_dict()
            model.row_count = table.row_count
            model.updated_at = table.updated_at
            await self.session.flush()
            return self._to_entity(model)

        return table

    async def delete(self, table_id: UUID) -> None:
        """Delete a table."""
        stmt = select(DataTableModel).where(DataTableModel.id == table_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def list_by_vault(
        self,
        vault_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DataTable]:
        """List tables in a vault with pagination."""
        stmt = (
            select(DataTableModel)
            .where(DataTableModel.vault_id == vault_id)
            .order_by(DataTableModel.name)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def count_by_vault(self, vault_id: UUID) -> int:
        """Count tables in a vault."""
        stmt = (
            select(func.count())
            .select_from(DataTableModel)
            .where(DataTableModel.vault_id == vault_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update_row_count(self, table_id: UUID, count: int) -> None:
        """Update the row count for a table."""
        stmt = select(DataTableModel).where(DataTableModel.id == table_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.row_count = count
            await self.session.flush()

    async def increment_row_count(self, table_id: UUID, delta: int = 1) -> None:
        """Increment the row count for a table."""
        stmt = select(DataTableModel).where(DataTableModel.id == table_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.row_count = max(0, model.row_count + delta)
            await self.session.flush()

    def _to_entity(self, model: DataTableModel) -> DataTable:
        """Convert model to entity."""
        return DataTable(
            id=model.id,
            vault_id=model.vault_id,
            name=model.name,
            slug=model.slug,
            description=model.description,
            schema=TableSchema.from_dict(model.schema) if model.schema else TableSchema(),
            row_count=model.row_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: DataTable) -> DataTableModel:
        """Convert entity to model."""
        return DataTableModel(
            id=entity.id,
            vault_id=entity.vault_id,
            name=entity.name,
            slug=entity.slug,
            description=entity.description,
            schema=entity.schema.to_dict(),
            row_count=entity.row_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
