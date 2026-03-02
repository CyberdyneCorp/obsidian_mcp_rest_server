"""List rows use case."""

import logging
from typing import Any
from uuid import UUID

from app.application.dto.table_dto import RowDTO
from app.application.interfaces.repositories import (
    RowRepository,
    TableRepository,
    VaultRepository,
)
from app.application.use_cases.base import TableAccessMixin


class ListRowsUseCase(TableAccessMixin):
    """Use case for listing rows in a table."""

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
        limit: int = 100,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
        sort_column: str | None = None,
        sort_order: str = "asc",
        search_query: str | None = None,
    ) -> tuple[list[RowDTO], int]:
        """List rows in a table.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            table_slug: Table slug
            limit: Maximum number of rows to return
            offset: Number of rows to skip
            filters: Column filters
            sort_column: Column to sort by
            sort_order: Sort order ('asc' or 'desc')
            search_query: Full-text search query

        Returns:
            Tuple of (list of row DTOs, total count)

        Raises:
            VaultNotFoundError: If vault not found
            TableNotFoundError: If table not found
        """
        _, table = await self.get_table_or_raise(user_id, vault_slug, table_slug)

        # Handle full-text search
        if search_query:
            rows = await self.row_repo.search_fulltext(
                table.id,
                search_query,
                limit=limit,
            )
            total = len(rows)
        else:
            # Get rows with filtering
            rows = await self.row_repo.list_by_table(
                table.id,
                limit=limit,
                offset=offset,
                filters=filters,
                sort_column=sort_column,
                sort_order=sort_order,
            )
            total = await self.row_repo.count_by_table(table.id, filters=filters)

        # Convert to DTOs
        row_dtos = [RowDTO.from_entity(r) for r in rows]
        self._logger.debug(f"Listed {len(row_dtos)} rows from table={table_slug}")

        return row_dtos, total
