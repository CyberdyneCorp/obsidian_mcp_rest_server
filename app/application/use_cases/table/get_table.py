"""Get table use case."""

from uuid import UUID

from app.application.dto.table_dto import TableDTO
from app.application.interfaces.repositories import TableRepository, VaultRepository
from app.domain.exceptions import TableNotFoundError, VaultNotFoundError


class GetTableUseCase:
    """Use case for getting a table."""

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
    ) -> TableDTO:
        """Get a table by slug.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            table_slug: Table slug

        Returns:
            Table DTO

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

        return TableDTO.from_entity(table)
