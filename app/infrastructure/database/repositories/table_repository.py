"""PostgreSQL data table repository implementation."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.data_table import DataTable
from app.domain.value_objects.column_type import TableSchema
from app.infrastructure.database.models.data_table import DataTableModel
from app.infrastructure.database.repositories.base import BaseRepository


class PostgresTableRepository(BaseRepository[DataTable, DataTableModel]):
    """PostgreSQL implementation of TableRepository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    def _get_model_class(self) -> type[DataTableModel]:
        return DataTableModel

    async def get_by_slug(self, vault_id: UUID, slug: str) -> DataTable | None:
        """Get table by vault ID and slug."""
        return await self._get_one_by_filter(
            DataTableModel.vault_id == vault_id,
            DataTableModel.slug == slug,
        )

    async def update(self, table: DataTable) -> DataTable:
        """Update an existing table."""
        model = await self._get_model_by_id(table.id)

        if model:
            model.name = table.name
            model.slug = table.slug
            model.description = table.description
            model.schema = table.schema.to_dict()
            model.row_count = table.row_count
            model.updated_at = table.updated_at
            await self.session.flush()
            self._logger.info(f"Updated table id={table.id}")
            return self._to_entity(model)

        self._logger.warning(f"Cannot update table: not found with id={table.id}")
        return table

    async def list_by_vault(
        self,
        vault_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DataTable]:
        """List tables in a vault with pagination."""
        return await self._list_by_filter(
            DataTableModel.vault_id == vault_id,
            order_by=DataTableModel.name,
            limit=limit,
            offset=offset,
        )

    async def count_by_vault(self, vault_id: UUID) -> int:
        """Count tables in a vault."""
        return await self._count_by_filter(DataTableModel.vault_id == vault_id)

    async def update_row_count(self, table_id: UUID, count: int) -> None:
        """Update the row count for a table."""
        model = await self._get_model_by_id(table_id)
        if model:
            model.row_count = count
            await self.session.flush()
            self._logger.debug(f"Updated row count to {count} for table={table_id}")

    async def increment_row_count(self, table_id: UUID, delta: int = 1) -> None:
        """Increment the row count for a table."""
        model = await self._get_model_by_id(table_id)
        if model:
            model.row_count = max(0, model.row_count + delta)
            await self.session.flush()
            self._logger.debug(f"Incremented row count by {delta} for table={table_id}")

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
