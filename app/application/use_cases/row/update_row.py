"""Update row use case."""

import logging
from uuid import UUID

from app.application.dto.table_dto import RowDTO, RowUpdateDTO
from app.application.interfaces.repositories import (
    RowRepository,
    TableRepository,
    VaultRepository,
)
from app.application.use_cases.base import RowAccessMixin
from app.domain.exceptions import SchemaValidationError


class UpdateRowUseCase(RowAccessMixin):
    """Use case for updating a row."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        table_repo: TableRepository,
        row_repo: RowRepository,
    ) -> None:
        self.vault_repo = vault_repo
        self.table_repo = table_repo
        self.row_repo = row_repo
        self._logger = logging.getLogger(__name__)

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        table_slug: str,
        row_id: UUID,
        data: RowUpdateDTO,
    ) -> RowDTO:
        """Update a row.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            table_slug: Table slug
            row_id: Row ID
            data: Row update data

        Returns:
            Updated row DTO

        Raises:
            VaultNotFoundError: If vault not found
            TableNotFoundError: If table not found
            RowNotFoundError: If row not found
            SchemaValidationError: If data doesn't match schema
        """
        _, table, row = await self.get_row_or_raise(user_id, vault_slug, table_slug, row_id)

        # Merge new data with existing
        if data.data is not None:
            merged_data = {**row.data, **data.data}

            # Validate merged data against schema
            is_valid, errors = table.validate_row_data(merged_data)
            if not is_valid:
                raise SchemaValidationError(errors)

            row.update_data(merged_data)

        # Persist changes
        row = await self.row_repo.update(row)
        self._logger.info(f"Updated row id={row_id}")

        return RowDTO.from_entity(row)
