"""Base use case with common validation helpers."""

import logging
from uuid import UUID

from app.application.interfaces.repositories import (
    RowRepository,
    TableRepository,
    VaultRepository,
)
from app.domain.entities.data_table import DataTable
from app.domain.entities.table_row import TableRow
from app.domain.entities.vault import Vault
from app.domain.exceptions import (
    RowNotFoundError,
    TableNotFoundError,
    VaultNotFoundError,
)


class BaseUseCase:
    """Base class for use cases providing common functionality."""

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__module__)


class VaultAccessMixin:
    """Mixin providing vault access validation.

    Use cases that need to validate vault access should inherit from this mixin
    and pass vault_repo in their __init__.
    """

    vault_repo: VaultRepository

    async def get_vault_or_raise(self, user_id: UUID, vault_slug: str) -> Vault:
        """Get vault by slug or raise VaultNotFoundError.

        Args:
            user_id: The user ID
            vault_slug: The vault slug

        Returns:
            The vault entity

        Raises:
            VaultNotFoundError: If vault not found or doesn't belong to user
        """
        vault = await self.vault_repo.get_by_slug(user_id, vault_slug)
        if not vault:
            raise VaultNotFoundError(slug=vault_slug)
        return vault


class TableAccessMixin(VaultAccessMixin):
    """Mixin providing table access validation.

    Extends VaultAccessMixin to also validate table access.
    Use cases should pass both vault_repo and table_repo in their __init__.
    """

    table_repo: TableRepository

    async def get_table_or_raise(
        self,
        user_id: UUID,
        vault_slug: str,
        table_slug: str,
    ) -> tuple[Vault, DataTable]:
        """Get vault and table or raise appropriate error.

        Args:
            user_id: The user ID
            vault_slug: The vault slug
            table_slug: The table slug

        Returns:
            Tuple of (vault, table) entities

        Raises:
            VaultNotFoundError: If vault not found
            TableNotFoundError: If table not found
        """
        vault = await self.get_vault_or_raise(user_id, vault_slug)

        table = await self.table_repo.get_by_slug(vault.id, table_slug)
        if not table:
            raise TableNotFoundError(slug=table_slug)

        return vault, table


class RowAccessMixin(TableAccessMixin):
    """Mixin providing row access validation.

    Extends TableAccessMixin to also validate row access.
    Use cases should pass vault_repo, table_repo, and row_repo in their __init__.
    """

    row_repo: RowRepository

    async def get_row_or_raise(
        self,
        user_id: UUID,
        vault_slug: str,
        table_slug: str,
        row_id: UUID,
    ) -> tuple[Vault, DataTable, TableRow]:
        """Get vault, table, and row or raise appropriate error.

        Args:
            user_id: The user ID
            vault_slug: The vault slug
            table_slug: The table slug
            row_id: The row ID

        Returns:
            Tuple of (vault, table, row) entities

        Raises:
            VaultNotFoundError: If vault not found
            TableNotFoundError: If table not found
            RowNotFoundError: If row not found or belongs to different table
        """
        vault, table = await self.get_table_or_raise(user_id, vault_slug, table_slug)

        row = await self.row_repo.get_by_id(row_id)
        if not row or row.table_id != table.id:
            raise RowNotFoundError(str(row_id))

        return vault, table, row
