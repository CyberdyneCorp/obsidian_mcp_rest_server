"""PostgreSQL document repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.document import Document
from app.domain.value_objects.frontmatter import Frontmatter
from app.infrastructure.database.models.document import DocumentModel
from app.infrastructure.database.repositories.base import BaseRepository


class PostgresDocumentRepository(BaseRepository[Document, DocumentModel]):
    """PostgreSQL implementation of DocumentRepository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    def _get_model_class(self) -> type[DocumentModel]:
        return DocumentModel

    async def get_by_path(self, vault_id: UUID, path: str) -> Document | None:
        """Get document by vault ID and path."""
        return await self._get_one_by_filter(
            DocumentModel.vault_id == vault_id,
            DocumentModel.path == path,
        )

    async def update(self, document: Document) -> Document:
        """Update an existing document."""
        model = await self._get_model_by_id(document.id)

        if model:
            model.title = document.title
            model.content = document.content
            model.content_hash = document.content_hash
            model.frontmatter = document.frontmatter.to_dict()
            model.aliases = document.aliases
            model.word_count = document.word_count
            model.link_count = document.link_count
            model.backlink_count = document.backlink_count
            model.updated_at = document.updated_at
            await self.session.flush()
            self._logger.info(f"Updated document id={document.id}")
            return self._to_entity(model)

        self._logger.warning(f"Cannot update document: not found with id={document.id}")
        return document

    async def list_by_vault(
        self,
        vault_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        """List documents in a vault with pagination."""
        return await self._list_by_filter(
            DocumentModel.vault_id == vault_id,
            order_by=DocumentModel.path,
            limit=limit,
            offset=offset,
        )

    async def list_by_folder(self, folder_id: UUID) -> list[Document]:
        """List documents in a specific folder."""
        return await self._list_by_filter(
            DocumentModel.folder_id == folder_id,
            order_by=DocumentModel.title,
        )

    async def count_by_vault(self, vault_id: UUID) -> int:
        """Count documents in a vault."""
        return await self._count_by_filter(DocumentModel.vault_id == vault_id)

    async def search_fulltext(
        self,
        vault_id: UUID,
        query: str,
        limit: int = 20,
    ) -> list[Document]:
        """Full-text search documents."""
        stmt = (
            select(DocumentModel)
            .where(
                DocumentModel.vault_id == vault_id,
                DocumentModel.content.ilike(f"%{query}%"),
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        self._logger.debug(f"Fulltext search for '{query}' found {len(models)} documents")
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: DocumentModel) -> Document:
        """Convert model to entity."""
        return Document(
            id=model.id,
            vault_id=model.vault_id,
            folder_id=model.folder_id,
            title=model.title,
            filename=model.filename,
            path=model.path,
            content=model.content,
            content_hash=model.content_hash,
            frontmatter=Frontmatter.from_dict(model.frontmatter),
            aliases=list(model.aliases) if model.aliases else [],
            word_count=model.word_count,
            link_count=model.link_count,
            backlink_count=model.backlink_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Document) -> DocumentModel:
        """Convert entity to model."""
        return DocumentModel(
            id=entity.id,
            vault_id=entity.vault_id,
            folder_id=entity.folder_id,
            title=entity.title,
            filename=entity.filename,
            path=entity.path,
            content=entity.content,
            content_hash=entity.content_hash,
            frontmatter=entity.frontmatter.to_dict(),
            aliases=entity.aliases,
            word_count=entity.word_count,
            link_count=entity.link_count,
            backlink_count=entity.backlink_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
