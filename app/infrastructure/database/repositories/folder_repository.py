"""PostgreSQL folder repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.folder import Folder
from app.infrastructure.database.models.folder import FolderModel


class PostgresFolderRepository:
    """PostgreSQL implementation of FolderRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, folder_id: UUID) -> Folder | None:
        """Get folder by ID."""
        stmt = select(FolderModel).where(FolderModel.id == folder_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_path(self, vault_id: UUID, path: str) -> Folder | None:
        """Get folder by vault ID and path."""
        stmt = select(FolderModel).where(
            FolderModel.vault_id == vault_id,
            FolderModel.path == path,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, folder: Folder) -> Folder:
        """Create a new folder."""
        model = self._to_model(folder)
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def create_many(self, folders: list[Folder]) -> list[Folder]:
        """Create multiple folders."""
        models = [self._to_model(f) for f in folders]
        self.session.add_all(models)
        await self.session.flush()
        return [self._to_entity(m) for m in models]

    async def delete(self, folder_id: UUID) -> None:
        """Delete a folder."""
        stmt = select(FolderModel).where(FolderModel.id == folder_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def list_by_vault(self, vault_id: UUID) -> list[Folder]:
        """List all folders in a vault."""
        stmt = select(FolderModel).where(FolderModel.vault_id == vault_id).order_by(FolderModel.path)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_or_create_path(self, vault_id: UUID, path: str) -> Folder:
        """Get or create a folder at the given path (including parents)."""
        # Check if already exists
        existing = await self.get_by_path(vault_id, path)
        if existing:
            return existing

        # Create parent folders first
        parts = path.split("/")
        parent_id = None

        for i in range(len(parts)):
            current_path = "/".join(parts[: i + 1])

            existing = await self.get_by_path(vault_id, current_path)
            if existing:
                parent_id = existing.id
                continue

            folder = Folder(
                vault_id=vault_id,
                parent_id=parent_id,
                name=parts[i],
                path=current_path,
                depth=i,
            )
            folder = await self.create(folder)
            parent_id = folder.id

        # Return the final folder
        final = await self.get_by_path(vault_id, path)
        assert final is not None
        return final

    def _to_entity(self, model: FolderModel) -> Folder:
        """Convert model to entity."""
        return Folder(
            id=model.id,
            vault_id=model.vault_id,
            parent_id=model.parent_id,
            name=model.name,
            path=model.path,
            depth=model.depth,
        )

    def _to_model(self, entity: Folder) -> FolderModel:
        """Convert entity to model."""
        return FolderModel(
            id=entity.id,
            vault_id=entity.vault_id,
            parent_id=entity.parent_id,
            name=entity.name,
            path=entity.path,
            depth=entity.depth,
        )
