"""List vaults use case."""

import logging
from uuid import UUID

from app.application.dto.vault_dto import VaultDTO
from app.application.interfaces.repositories import VaultRepository


class ListVaultsUseCase:
    """Use case for listing user's vaults."""

    def __init__(self, vault_repo: VaultRepository) -> None:
        self.vault_repo = vault_repo
        self._logger = logging.getLogger(__name__)

    async def execute(self, user_id: UUID) -> list[VaultDTO]:
        """List all vaults for a user.

        Args:
            user_id: User ID

        Returns:
            List of vault DTOs
        """
        vaults = await self.vault_repo.list_by_user(user_id)
        self._logger.debug(f"Listed {len(vaults)} vaults for user={user_id}")
        return [VaultDTO.from_entity(v) for v in vaults]
