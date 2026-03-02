"""PostgreSQL tag repository implementation."""

from uuid import UUID

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.tag import Tag
from app.infrastructure.database.models.tag import TagModel
from app.infrastructure.database.repositories.base import BaseRepository


class PostgresTagRepository(BaseRepository[Tag, TagModel]):
    """PostgreSQL implementation of TagRepository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    def _get_model_class(self) -> type[TagModel]:
        return TagModel

    async def get_by_name(self, vault_id: UUID, name: str) -> Tag | None:
        """Get tag by vault ID and name."""
        slug = slugify(name.lstrip("#"), separator="-")
        stmt = select(TagModel).where(
            TagModel.vault_id == vault_id,
            TagModel.slug == slug,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            self._logger.debug(f"Found tag with name={name} in vault={vault_id}")
            return self._to_entity(model)
        return None

    async def get_or_create(self, vault_id: UUID, name: str) -> Tag:
        """Get existing tag or create new one."""
        existing = await self.get_by_name(vault_id, name)
        if existing:
            return existing

        tag = Tag.create(vault_id=vault_id, name=name)
        created = await self.create(tag)
        self._logger.info(f"Created tag name={name} in vault={vault_id}")
        return created

    async def update(self, tag: Tag) -> Tag:
        """Update an existing tag."""
        model = await self._get_model_by_id(tag.id)

        if model:
            model.name = tag.name
            model.slug = tag.slug
            model.parent_tag_id = tag.parent_tag_id
            model.document_count = tag.document_count
            await self.session.flush()
            self._logger.info(f"Updated tag id={tag.id}")
            return self._to_entity(model)

        self._logger.warning(f"Cannot update tag: not found with id={tag.id}")
        return tag

    async def list_by_vault(self, vault_id: UUID) -> list[Tag]:
        """List all tags in a vault."""
        stmt = select(TagModel).where(TagModel.vault_id == vault_id).order_by(TagModel.name)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        self._logger.debug(f"Listed {len(models)} tags in vault={vault_id}")
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
