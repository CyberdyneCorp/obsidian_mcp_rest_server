"""Update table use case."""

import logging
from uuid import UUID

from app.application.dto.table_dto import TableDTO, TableUpdateDTO
from app.application.interfaces.repositories import TableRepository, VaultRepository
from app.application.use_cases.base import TableAccessMixin
from app.domain.value_objects.column_type import TableSchema


class UpdateTableUseCase(TableAccessMixin):
    """Use case for updating a table."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        table_repo: TableRepository,
    ) -> None:
        self.vault_repo = vault_repo
        self.table_repo = table_repo
        self._logger = logging.getLogger(__name__)

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        table_slug: str,
        data: TableUpdateDTO,
    ) -> TableDTO:
        """Update a table.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            table_slug: Table slug
            data: Table update data

        Returns:
            Updated table DTO

        Raises:
            VaultNotFoundError: If vault not found
            TableNotFoundError: If table not found
        """
        _, table = await self.get_table_or_raise(user_id, vault_slug, table_slug)

        # Update fields
        if data.name is not None:
            table.update_name(data.name)

        if data.description is not None:
            table.update_description(data.description)

        if data.columns is not None:
            new_schema = TableSchema.from_list(data.columns)
            table.update_schema(new_schema)

        # Persist changes
        table = await self.table_repo.update(table)
        self._logger.info(f"Updated table slug={table_slug}")

        return TableDTO.from_entity(table)
