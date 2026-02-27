"""Get vault use case."""

from uuid import UUID

from app.application.dto.vault_dto import VaultDTO
from app.application.interfaces.repositories import VaultRepository
from app.domain.exceptions import VaultNotFoundError


class GetVaultUseCase:
    """Use case for getting a vault by slug."""

    def __init__(self, vault_repo: VaultRepository) -> None:
        self.vault_repo = vault_repo

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
        vault = await self.vault_repo.get_by_slug(user_id, slug)
        if not vault:
            raise VaultNotFoundError(slug=slug)

        return VaultDTO.from_entity(vault)
