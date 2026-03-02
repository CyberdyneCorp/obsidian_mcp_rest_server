"""Get vault use case."""

import logging
from uuid import UUID

from app.application.dto.vault_dto import VaultDTO
from app.application.interfaces.repositories import VaultRepository
from app.application.use_cases.base import VaultAccessMixin


class GetVaultUseCase(VaultAccessMixin):
    """Use case for getting a vault by slug."""

    def __init__(self, vault_repo: VaultRepository) -> None:
        self.vault_repo = vault_repo
        self._logger = logging.getLogger(__name__)

    async def execute(self, user_id: UUID, slug: str) -> VaultDTO:
        """Get a vault by slug.

        Args:
            user_id: User ID
            slug: Vault slug

        Returns:
            Vault DTO

        Raises:
            VaultNotFoundError: If vault not found
        """
        vault = await self.get_vault_or_raise(user_id, slug)
        self._logger.debug(f"Retrieved vault slug={slug}")

        return VaultDTO.from_entity(vault)
