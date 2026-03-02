"""Get row use case."""

import logging
from uuid import UUID

from app.application.dto.table_dto import RowDTO
from app.application.interfaces.repositories import (
    RowRepository,
    TableRepository,
    VaultRepository,
)
from app.application.use_cases.base import RowAccessMixin


class GetRowUseCase(RowAccessMixin):
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
        self._logger = logging.getLogger(__name__)

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
        _, _, row = await self.get_row_or_raise(user_id, vault_slug, table_slug, row_id)
        self._logger.debug(f"Retrieved row id={row_id}")

        return RowDTO.from_entity(row)
