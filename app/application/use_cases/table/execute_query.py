"""Execute query use case."""

from typing import Any
from uuid import UUID

from app.application.interfaces.repositories import (
    RowRepository,
    TableRepository,
    VaultRepository,
)
from app.domain.exceptions import QueryParseError, TableNotFoundError, VaultNotFoundError
from app.domain.services.query_parser import QueryParserService


class ExecuteQueryUseCase:
    """Use case for executing dataview-style queries."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        table_repo: TableRepository,
        row_repo: RowRepository,
    ) -> None:
        self.vault_repo = vault_repo
        self.table_repo = table_repo
        self.row_repo = row_repo
        self.query_parser = QueryParserService()

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        query_string: str,
    ) -> dict[str, Any]:
        """Execute a dataview-style query.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            query_string: Dataview-style query

        Returns:
            Query results with columns and rows

        Raises:
            VaultNotFoundError: If vault not found
            TableNotFoundError: If table not found
            QueryParseError: If query syntax is invalid
        """
        # Get vault
        vault = await self.vault_repo.get_by_slug(user_id, vault_slug)
        if not vault:
            raise VaultNotFoundError(slug=vault_slug)

        # Parse query
        parsed = self.query_parser.parse(query_string)

        # Get table
        table = await self.table_repo.get_by_slug(vault.id, parsed.table_name)
        if not table:
            raise TableNotFoundError(slug=parsed.table_name)

        # Build filters
        filters = self.query_parser.to_filter_dict(parsed)

        # Get sort parameters
        sort_column = None
        sort_order = "asc"
        if parsed.sort_clauses:
            sort_column = parsed.sort_clauses[0].column
            sort_order = parsed.sort_clauses[0].order.value.lower()

        # Execute query
        rows = await self.row_repo.list_by_table(
            table.id,
            limit=parsed.limit or 100,
            offset=parsed.offset or 0,
            filters=filters if filters else None,
            sort_column=sort_column,
            sort_order=sort_order,
        )

        # Get total count
        total = await self.row_repo.count_by_table(
            table.id,
            filters=filters if filters else None,
        )

        # Determine columns to return
        if parsed.columns:
            columns = parsed.columns
        else:
            columns = table.column_names

        # Build result rows
        result_rows = []
        for row in rows:
            row_data = {"id": str(row.id)}
            for col in columns:
                row_data[col] = row.data.get(col)
            result_rows.append(row_data)

        return {
            "columns": columns,
            "rows": result_rows,
            "total": total,
            "limit": parsed.limit or 100,
            "offset": parsed.offset or 0,
        }
