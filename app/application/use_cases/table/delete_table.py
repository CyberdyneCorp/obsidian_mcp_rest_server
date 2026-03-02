"""Delete table use case."""

import logging
from uuid import UUID

from app.application.interfaces.repositories import TableRepository, VaultRepository
from app.application.use_cases.base import TableAccessMixin


class DeleteTableUseCase(TableAccessMixin):
    """Use case for deleting a table."""

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
    ) -> None:
        """Delete a table.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            table_slug: Table slug

        Raises:
            VaultNotFoundError: If vault not found
            TableNotFoundError: If table not found
        """
        _, table = await self.get_table_or_raise(user_id, vault_slug, table_slug)

        # Delete table (cascades to rows)
        await self.table_repo.delete(table.id)
        self._logger.info(f"Deleted table slug={table_slug}")
