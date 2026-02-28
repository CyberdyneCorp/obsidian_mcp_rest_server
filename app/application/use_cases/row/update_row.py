"""Update row use case."""

from uuid import UUID

from app.application.dto.table_dto import RowDTO, RowUpdateDTO
from app.application.interfaces.repositories import (
    RowRepository,
    TableRepository,
    VaultRepository,
)
from app.domain.exceptions import (
    RowNotFoundError,
    SchemaValidationError,
    TableNotFoundError,
    VaultNotFoundError,
)


class UpdateRowUseCase:
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
        # Get vault
        vault = await self.vault_repo.get_by_slug(user_id, vault_slug)
        if not vault:
            raise VaultNotFoundError(slug=vault_slug)

        # Get table
        table = await self.table_repo.get_by_slug(vault.id, table_slug)
        if not table:
            raise TableNotFoundError(slug=table_slug)

        # Get row
        row = await self.row_repo.get_by_id(row_id)
        if not row or row.table_id != table.id:
            raise RowNotFoundError(str(row_id))

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

        return RowDTO.from_entity(row)
