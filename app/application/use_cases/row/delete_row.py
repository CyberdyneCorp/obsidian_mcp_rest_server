"""Delete row use case."""

from uuid import UUID

from app.application.interfaces.repositories import (
    RelationshipRepository,
    RowRepository,
    TableRepository,
    VaultRepository,
)
from app.domain.exceptions import RowNotFoundError, TableNotFoundError, VaultNotFoundError
from app.domain.services.referential_integrity import ReferentialIntegrityService


class DeleteRowUseCase:
    """Use case for deleting a row."""

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
        row_id: UUID,
    ) -> None:
        """Delete a row.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            table_slug: Table slug
            row_id: Row ID

        Raises:
            VaultNotFoundError: If vault not found
            TableNotFoundError: If table not found
            RowNotFoundError: If row not found
            ReferentialIntegrityError: If RESTRICT constraint prevents deletion
        """
        # Get vault
        vault = await self.vault_repo.get_by_slug(user_id, vault_slug)
        if not vault:
            raise VaultNotFoundError(slug=vault_slug)

        # Get table
        table = await self.table_repo.get_by_slug(vault.id, table_slug)
        if not table:
            raise TableNotFoundError(slug=table_slug)

        # Get row
        row = await self.row_repo.get_by_id(row_id)
        if not row or row.table_id != table.id:
            raise RowNotFoundError(str(row_id))

        # Handle referential integrity (CASCADE, SET NULL, RESTRICT)
        if self.relationship_repo:
            integrity_service = ReferentialIntegrityService(
                self.relationship_repo,
                self.table_repo,
                self.row_repo,
            )
            await integrity_service.handle_row_deletion(table.id, row_id)

        # Delete row
        await self.row_repo.delete(row_id)

        # Update table row count
        await self.table_repo.increment_row_count(table.id, -1)
