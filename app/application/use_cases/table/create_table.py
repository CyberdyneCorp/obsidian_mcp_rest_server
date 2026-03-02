"""Create table use case."""

import logging
from uuid import UUID

from app.application.dto.table_dto import TableCreateDTO, TableDTO
from app.application.interfaces.repositories import TableRepository, VaultRepository
from app.application.use_cases.base import VaultAccessMixin
from app.domain.entities.data_table import DataTable
from app.domain.exceptions import DuplicateTableError


class CreateTableUseCase(VaultAccessMixin):
    """Use case for creating a new table."""

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
        data: TableCreateDTO,
    ) -> TableDTO:
        """Create a new table.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            data: Table creation data

        Returns:
            Created table DTO

        Raises:
            VaultNotFoundError: If vault not found
            DuplicateTableError: If table slug already exists
        """
        vault = await self.get_vault_or_raise(user_id, vault_slug)

        # Create table entity
        table = DataTable.create(
            vault_id=vault.id,
            name=data.name,
            columns=data.columns,
            description=data.description,
            slug=data.slug,
        )

        # Check for duplicate slug
        existing = await self.table_repo.get_by_slug(vault.id, table.slug)
        if existing:
            raise DuplicateTableError(table.slug)

        # Persist table
        table = await self.table_repo.create(table)
        self._logger.info(f"Created table '{table.name}' in vault={vault_slug}")

        return TableDTO.from_entity(table)
