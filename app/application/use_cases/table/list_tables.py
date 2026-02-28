"""List tables use case."""

from uuid import UUID

from app.application.dto.table_dto import TableSummaryDTO
from app.application.interfaces.repositories import TableRepository, VaultRepository
from app.domain.exceptions import VaultNotFoundError


class ListTablesUseCase:
    """Use case for listing tables in a vault."""

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
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[TableSummaryDTO], int]:
        """List tables in a vault.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            limit: Maximum number of tables to return
            offset: Number of tables to skip

        Returns:
            Tuple of (list of table summary DTOs, total count)

        Raises:
            VaultNotFoundError: If vault not found
        """
        # Get vault
        vault = await self.vault_repo.get_by_slug(user_id, vault_slug)
        if not vault:
            raise VaultNotFoundError(slug=vault_slug)

        # Get tables
        tables = await self.table_repo.list_by_vault(vault.id, limit=limit, offset=offset)
        total = await self.table_repo.count_by_vault(vault.id)

        # Convert to DTOs
        table_dtos = [TableSummaryDTO.from_entity(t) for t in tables]

        return table_dtos, total
