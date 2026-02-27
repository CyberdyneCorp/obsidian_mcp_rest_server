"""PostgreSQL tag repository implementation."""

from uuid import UUID

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.tag import Tag
from app.infrastructure.database.models.tag import TagModel


class PostgresTagRepository:
    """PostgreSQL implementation of TagRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, tag_id: UUID) -> Tag | None:
        """Get tag by ID."""
        stmt = select(TagModel).where(TagModel.id == tag_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_name(self, vault_id: UUID, name: str) -> Tag | None:
        """Get tag by vault ID and name."""
        slug = slugify(name.lstrip("#"), separator="-")
        stmt = select(TagModel).where(
            TagModel.vault_id == vault_id,
            TagModel.slug == slug,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, tag: Tag) -> Tag:
        """Create a new tag."""
        model = self._to_model(tag)
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def get_or_create(self, vault_id: UUID, name: str) -> Tag:
        """Get existing tag or create new one."""
        existing = await self.get_by_name(vault_id, name)
        if existing:
            return existing

        tag = Tag.create(vault_id=vault_id, name=name)
        return await self.create(tag)

    async def update(self, tag: Tag) -> Tag:
        """Update an existing tag."""
        stmt = select(TagModel).where(TagModel.id == tag.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.name = tag.name
            model.slug = tag.slug
            model.parent_tag_id = tag.parent_tag_id
            model.document_count = tag.document_count
            await self.session.flush()
            return self._to_entity(model)

        return tag

    async def delete(self, tag_id: UUID) -> None:
        """Delete a tag."""
        stmt = select(TagModel).where(TagModel.id == tag_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def list_by_vault(self, vault_id: UUID) -> list[Tag]:
        """List all tags in a vault."""
        stmt = select(TagModel).where(TagModel.vault_id == vault_id).order_by(TagModel.name)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: TagModel) -> Tag:
        """Convert model to entity."""
        return Tag(
            id=model.id,
            vault_id=model.vault_id,
            name=model.name,
            slug=model.slug,
            parent_tag_id=model.parent_tag_id,
            document_count=model.document_count,
        )

    def _to_model(self, entity: Tag) -> TagModel:
        """Convert entity to model."""
        return TagModel(
            id=entity.id,
            vault_id=entity.vault_id,
            name=entity.name,
            slug=entity.slug,
            parent_tag_id=entity.parent_tag_id,
            document_count=entity.document_count,
        )
