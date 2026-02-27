"""PostgreSQL document repository implementation."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.document import Document
from app.domain.value_objects.frontmatter import Frontmatter
from app.infrastructure.database.models.document import DocumentModel


class PostgresDocumentRepository:
    """PostgreSQL implementation of DocumentRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, document_id: UUID) -> Document | None:
        """Get document by ID."""
        stmt = select(DocumentModel).where(DocumentModel.id == document_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_path(self, vault_id: UUID, path: str) -> Document | None:
        """Get document by vault ID and path."""
        stmt = select(DocumentModel).where(
            DocumentModel.vault_id == vault_id,
            DocumentModel.path == path,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, document: Document) -> Document:
        """Create a new document."""
        model = self._to_model(document)
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def create_many(self, documents: list[Document]) -> list[Document]:
        """Create multiple documents."""
        models = [self._to_model(d) for d in documents]
        self.session.add_all(models)
        await self.session.flush()
        return [self._to_entity(m) for m in models]

    async def update(self, document: Document) -> Document:
        """Update an existing document."""
        stmt = select(DocumentModel).where(DocumentModel.id == document.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

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
            return self._to_entity(model)

        return document

    async def delete(self, document_id: UUID) -> None:
        """Delete a document."""
        stmt = select(DocumentModel).where(DocumentModel.id == document_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def list_by_vault(
        self,
        vault_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        """List documents in a vault with pagination."""
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.vault_id == vault_id)
            .order_by(DocumentModel.path)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def list_by_folder(self, folder_id: UUID) -> list[Document]:
        """List documents in a specific folder."""
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.folder_id == folder_id)
            .order_by(DocumentModel.title)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def count_by_vault(self, vault_id: UUID) -> int:
        """Count documents in a vault."""
        stmt = select(func.count()).select_from(DocumentModel).where(DocumentModel.vault_id == vault_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def search_fulltext(
        self,
        vault_id: UUID,
        query: str,
        limit: int = 20,
    ) -> list[Document]:
        """Full-text search documents."""
        # Simple ILIKE search for now - can be enhanced with tsvector
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
