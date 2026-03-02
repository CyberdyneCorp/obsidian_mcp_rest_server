"""Export CSV use case."""

import logging
from uuid import UUID

from app.application.interfaces.repositories import (
    RowRepository,
    TableRepository,
    VaultRepository,
)
from app.application.use_cases.base import TableAccessMixin
from app.domain.services.csv_parser import CsvParserService


class ExportCsvUseCase(TableAccessMixin):
    """Use case for exporting table data to CSV."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        table_repo: TableRepository,
        row_repo: RowRepository,
    ) -> None:
        self.vault_repo = vault_repo
        self.table_repo = table_repo
        self.row_repo = row_repo
        self.csv_parser = CsvParserService()
        self._logger = logging.getLogger(__name__)

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        table_slug: str,
        delimiter: str = ",",
    ) -> tuple[str, str]:
        """Export table data to CSV.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            table_slug: Table slug
            delimiter: CSV delimiter

        Returns:
            Tuple of (CSV content, suggested filename)

        Raises:
            VaultNotFoundError: If vault not found
            TableNotFoundError: If table not found
        """
        _, table = await self.get_table_or_raise(user_id, vault_slug, table_slug)

        # Get all rows (no pagination for export)
        rows = await self.row_repo.list_by_table(
            table.id,
            limit=100000,  # High limit for export
            offset=0,
        )

        # Get column names in order
        columns = table.column_names

        # Convert rows to dicts
        row_dicts = [row.data for row in rows]

        # Generate CSV
        csv_content = self.csv_parser.export_csv(
            columns,
            row_dicts,
            delimiter=delimiter,
        )

        filename = f"{table.slug}.csv"
        self._logger.info(f"Exported {len(rows)} rows from table={table_slug}")

        return csv_content, filename
