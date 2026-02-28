"""Create row use case."""

from uuid import UUID

from app.application.dto.table_dto import RowCreateDTO, RowDTO
from app.application.interfaces.repositories import (
    RelationshipRepository,
    RowRepository,
    TableRepository,
    VaultRepository,
)
from app.domain.entities.table_row import TableRow
from app.domain.exceptions import SchemaValidationError, TableNotFoundError, VaultNotFoundError
from app.domain.services.referential_integrity import ReferentialIntegrityService


class CreateRowUseCase:
    """Use case for creating a new row."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        table_repo: TableRepository,
        row_repo: RowRepository,
        relationship_repo: RelationshipRepository | None = None,
    ) -> None:
        self.vault_repo = vault_repo
        self.table_repo = table_repo
        self.row_repo = row_repo
        self.relationship_repo = relationship_repo

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        table_slug: str,
        data: RowCreateDTO,
    ) -> RowDTO:
        """Create a new row.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            table_slug: Table slug
            data: Row creation data

        Returns:
            Created row DTO

        Raises:
            VaultNotFoundError: If vault not found
            TableNotFoundError: If table not found
            SchemaValidationError: If data doesn't match schema
            ReferentialIntegrityError: If references are invalid
        """
        # Get vault
        vault = await self.vault_repo.get_by_slug(user_id, vault_slug)
        if not vault:
            raise VaultNotFoundError(slug=vault_slug)

        # Get table
        table = await self.table_repo.get_by_slug(vault.id, table_slug)
        if not table:
            raise TableNotFoundError(slug=table_slug)

        # Validate data against schema
        is_valid, errors = table.validate_row_data(data.data)
        if not is_valid:
            raise SchemaValidationError(errors)

        # Apply defaults for missing columns
        row_data = dict(data.data)
        for column in table.schema.columns:
            if column.name not in row_data and column.default is not None:
                row_data[column.name] = column.default

        # Validate foreign key references
        if self.relationship_repo:
            integrity_service = ReferentialIntegrityService(
                self.relationship_repo,
                self.table_repo,
                self.row_repo,
            )
            await integrity_service.validate_references(table.id, row_data)

        # Create row
        row = TableRow.create(
            table_id=table.id,
            vault_id=vault.id,
            data=row_data,
        )

        row = await self.row_repo.create(row)

        # Update table row count
        await self.table_repo.increment_row_count(table.id, 1)

        return RowDTO.from_entity(row)
