"""Get row use case."""

from uuid import UUID

from app.application.dto.table_dto import RowDTO
from app.application.interfaces.repositories import (
    RowRepository,
    TableRepository,
    VaultRepository,
)
from app.domain.exceptions import RowNotFoundError, TableNotFoundError, VaultNotFoundError


class GetRowUseCase:
    """Use case for getting a row."""

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
    ) -> RowDTO:
        """Get a row by ID.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            table_slug: Table slug
            row_id: Row ID

        Returns:
            Row DTO

        Raises:
            VaultNotFoundError: If vault not found
            TableNotFoundError: If table not found
            RowNotFoundError: If row not found
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

        return RowDTO.from_entity(row)
