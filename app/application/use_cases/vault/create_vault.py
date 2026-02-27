"""Create vault use case."""

from uuid import UUID

from app.application.dto.vault_dto import VaultCreateDTO, VaultDTO
from app.application.interfaces.repositories import VaultRepository
from app.domain.entities.vault import Vault
from app.domain.exceptions import DuplicateVaultError


class CreateVaultUseCase:
    """Use case for creating a new vault."""

    def __init__(self, vault_repo: VaultRepository) -> None:
        self.vault_repo = vault_repo

    async def execute(
        self,
        user_id: UUID,
        data: VaultCreateDTO,
    ) -> VaultDTO:
        """Create a new vault.

        Args:
            user_id: Owner user ID
            data: Vault creation data

        Returns:
            Created vault DTO

        Raises:
            DuplicateVaultError: If vault with same slug exists
        """
        # Create vault entity
        vault = Vault.create(
            user_id=user_id,
            name=data.name,
            description=data.description,
        )

        # Check for duplicate slug
        existing = await self.vault_repo.get_by_slug(user_id, vault.slug)
        if existing:
            raise DuplicateVaultError(vault.slug)

        # Save vault
        vault = await self.vault_repo.create(vault)

        return VaultDTO.from_entity(vault)
