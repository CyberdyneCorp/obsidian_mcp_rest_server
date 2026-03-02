"""Delete vault use case."""

import logging
from uuid import UUID

from app.application.interfaces.graph_provider import GraphProvider
from app.application.interfaces.repositories import VaultRepository
from app.application.interfaces.storage import StorageProvider
from app.application.use_cases.base import VaultAccessMixin


class DeleteVaultUseCase(VaultAccessMixin):
    """Use case for deleting a vault."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        graph_provider: GraphProvider | None = None,
        storage_provider: StorageProvider | None = None,
    ) -> None:
        self.vault_repo = vault_repo
        self.graph_provider = graph_provider
        self.storage_provider = storage_provider
        self._logger = logging.getLogger(__name__)

    async def execute(self, user_id: UUID, slug: str) -> None:
        """Delete a vault and all its contents.

        Args:
            user_id: User ID
            slug: Vault slug

        Raises:
            VaultNotFoundError: If vault not found
        """
        vault = await self.get_vault_or_raise(user_id, slug)

        # Delete storage files
        if self.storage_provider:
            await self.storage_provider.delete_vault_files(vault.id)

        # Delete vault (cascade deletes documents, links, etc.)
        await self.vault_repo.delete(vault.id)
        self._logger.info(f"Deleted vault slug={slug}")
