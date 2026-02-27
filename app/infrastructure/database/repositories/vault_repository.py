"""PostgreSQL vault repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.vault import Vault
from app.infrastructure.database.models.vault import VaultModel


class PostgresVaultRepository:
    """PostgreSQL implementation of VaultRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, vault_id: UUID) -> Vault | None:
        """Get vault by ID."""
        stmt = select(VaultModel).where(VaultModel.id == vault_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_slug(self, user_id: UUID, slug: str) -> Vault | None:
        """Get vault by user ID and slug."""
        stmt = select(VaultModel).where(
            VaultModel.user_id == user_id,
            VaultModel.slug == slug,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, vault: Vault) -> Vault:
        """Create a new vault."""
        model = self._to_model(vault)
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def update(self, vault: Vault) -> Vault:
        """Update an existing vault."""
        stmt = select(VaultModel).where(VaultModel.id == vault.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.name = vault.name
            model.slug = vault.slug
            model.description = vault.description
            model.document_count = vault.document_count
            model.updated_at = vault.updated_at
            await self.session.flush()
            return self._to_entity(model)

        return vault

    async def delete(self, vault_id: UUID) -> None:
        """Delete a vault and all its contents."""
        stmt = select(VaultModel).where(VaultModel.id == vault_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def list_by_user(self, user_id: UUID) -> list[Vault]:
        """List all vaults for a user."""
        stmt = select(VaultModel).where(VaultModel.user_id == user_id).order_by(VaultModel.name)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

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
