"""Import CSV use case."""

from uuid import UUID

from app.application.dto.table_dto import TableDTO
from app.application.interfaces.repositories import (
    RowRepository,
    TableRepository,
    VaultRepository,
)
from app.domain.entities.data_table import DataTable
from app.domain.entities.table_row import TableRow
from app.domain.exceptions import DuplicateTableError, TableNotFoundError, VaultNotFoundError
from app.domain.services.csv_parser import CsvParserService


class ImportCsvUseCase:
    """Use case for importing CSV data into a table."""

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

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        content: str | bytes,
        table_name: str | None = None,
        table_slug: str | None = None,
        delimiter: str = ",",
        has_header: bool = True,
    ) -> TableDTO:
        """Import CSV data into a new table.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            content: CSV content
            table_name: Name for the new table (required for new table)
            table_slug: Optional existing table slug to append to
            delimiter: CSV delimiter
            has_header: Whether CSV has header row

        Returns:
            Created or updated table DTO

        Raises:
            VaultNotFoundError: If vault not found
            DuplicateTableError: If table name already exists
            CsvParseError: If CSV parsing fails
        """
        # Get vault
        vault = await self.vault_repo.get_by_slug(user_id, vault_slug)
        if not vault:
            raise VaultNotFoundError(slug=vault_slug)

        # Parse CSV
        headers, rows = self.csv_parser.parse_csv(
            content,
            delimiter=delimiter,
            has_header=has_header,
        )

        if table_slug:
            # Append to existing table
            table = await self.table_repo.get_by_slug(vault.id, table_slug)
            if not table:
                raise TableNotFoundError(slug=table_slug)
        else:
            # Create new table with inferred schema
            if not table_name:
                table_name = "Imported Table"

            column_defs = self.csv_parser.infer_column_types(headers, rows)

            table = DataTable.create(
                vault_id=vault.id,
                name=table_name,
                columns=column_defs,
            )

            # Check for duplicate
            existing = await self.table_repo.get_by_slug(vault.id, table.slug)
            if existing:
                raise DuplicateTableError(table.slug)

            table = await self.table_repo.create(table)

        # Create rows
        row_entities = [
            TableRow.create(
                table_id=table.id,
                vault_id=vault.id,
                data=row_data,
            )
            for row_data in rows
        ]

        if row_entities:
            await self.row_repo.create_many(row_entities)

            # Update row count
            table.set_row_count(table.row_count + len(row_entities))
            await self.table_repo.update(table)

        return TableDTO.from_entity(table)


class AppendCsvUseCase:
    """Use case for appending CSV data to an existing table."""

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

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        table_slug: str,
        content: str | bytes,
        delimiter: str = ",",
        has_header: bool = True,
    ) -> tuple[int, int]:
        """Append CSV data to an existing table.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            table_slug: Table slug
            content: CSV content
            delimiter: CSV delimiter
            has_header: Whether CSV has header row

        Returns:
            Tuple of (rows imported, rows skipped)

        Raises:
            VaultNotFoundError: If vault not found
            TableNotFoundError: If table not found
            CsvParseError: If CSV parsing fails
        """
        # Get vault
        vault = await self.vault_repo.get_by_slug(user_id, vault_slug)
        if not vault:
            raise VaultNotFoundError(slug=vault_slug)

        # Get table
        table = await self.table_repo.get_by_slug(vault.id, table_slug)
        if not table:
            raise TableNotFoundError(slug=table_slug)

        # Parse CSV
        headers, rows = self.csv_parser.parse_csv(
            content,
            delimiter=delimiter,
            has_header=has_header,
        )

        # Filter rows to only include columns that exist in the table
        table_columns = set(table.column_names)
        valid_rows = []
        skipped = 0

        for row_data in rows:
            filtered_data = {k: v for k, v in row_data.items() if k in table_columns}

            # Validate against schema
            is_valid, _ = table.validate_row_data(filtered_data)
            if is_valid:
                valid_rows.append(filtered_data)
            else:
                skipped += 1

        # Create rows
        row_entities = [
            TableRow.create(
                table_id=table.id,
                vault_id=vault.id,
                data=row_data,
            )
            for row_data in valid_rows
        ]

        if row_entities:
            await self.row_repo.create_many(row_entities)

            # Update row count
            await self.table_repo.increment_row_count(table.id, len(row_entities))

        return len(row_entities), skipped
