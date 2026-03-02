"""PostgreSQL vault repository implementation."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.vault import Vault
from app.infrastructure.database.models.vault import VaultModel
from app.infrastructure.database.repositories.base import BaseRepository


class PostgresVaultRepository(BaseRepository[Vault, VaultModel]):
    """PostgreSQL implementation of VaultRepository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    def _get_model_class(self) -> type[VaultModel]:
        return VaultModel

    async def get_by_slug(self, user_id: UUID, slug: str) -> Vault | None:
        """Get vault by user ID and slug."""
        return await self._get_one_by_filter(
            VaultModel.user_id == user_id,
            VaultModel.slug == slug,
        )

    async def update(self, vault: Vault) -> Vault:
        """Update an existing vault."""
        model = await self._get_model_by_id(vault.id)

        if model:
            model.name = vault.name
            model.slug = vault.slug
            model.description = vault.description
            model.document_count = vault.document_count
            model.updated_at = vault.updated_at
            await self.session.flush()
            self._logger.info(f"Updated vault id={vault.id}")
            return self._to_entity(model)

        self._logger.warning(f"Cannot update vault: not found with id={vault.id}")
        return vault

    async def list_by_user(self, user_id: UUID) -> list[Vault]:
        """List all vaults for a user."""
        return await self._list_by_filter(
            VaultModel.user_id == user_id,
            order_by=VaultModel.name,
        )

    def _to_entity(self, model: VaultModel) -> Vault:
        """Convert model to entity."""
        return Vault(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            slug=model.slug,
            description=model.description,
            document_count=model.document_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Vault) -> VaultModel:
        """Convert entity to model."""
        return VaultModel(
            id=entity.id,
            user_id=entity.user_id,
            name=entity.name,
            slug=entity.slug,
            description=entity.description,
            document_count=entity.document_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
