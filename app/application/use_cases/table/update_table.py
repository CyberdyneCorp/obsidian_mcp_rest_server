"""Update table use case."""

from uuid import UUID

from app.application.dto.table_dto import TableDTO, TableUpdateDTO
from app.application.interfaces.repositories import TableRepository, VaultRepository
from app.domain.exceptions import TableNotFoundError, VaultNotFoundError
from app.domain.value_objects.column_type import TableSchema


class UpdateTableUseCase:
    """Use case for updating a table."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        table_repo: TableRepository,
    ) -> None:
        self.vault_repo = vault_repo
        self.table_repo = table_repo

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
        # Get vault
        vault = await self.vault_repo.get_by_slug(user_id, vault_slug)
        if not vault:
            raise VaultNotFoundError(slug=vault_slug)

        # Get table
        table = await self.table_repo.get_by_slug(vault.id, table_slug)
        if not table:
            raise TableNotFoundError(slug=table_slug)

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

        return TableDTO.from_entity(table)
