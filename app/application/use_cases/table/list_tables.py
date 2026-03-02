"""List tables use case."""

import logging
from uuid import UUID

from app.application.dto.table_dto import TableSummaryDTO
from app.application.interfaces.repositories import TableRepository, VaultRepository
from app.application.use_cases.base import VaultAccessMixin


class ListTablesUseCase(VaultAccessMixin):
    """Use case for listing tables in a vault."""

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
        vault = await self.get_vault_or_raise(user_id, vault_slug)

        # Get tables
        tables = await self.table_repo.list_by_vault(vault.id, limit=limit, offset=offset)
        total = await self.table_repo.count_by_vault(vault.id)

        # Convert to DTOs
        table_dtos = [TableSummaryDTO.from_entity(t) for t in tables]
        self._logger.debug(f"Listed {len(table_dtos)} tables in vault={vault_slug}")

        return table_dtos, total
