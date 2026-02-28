"""PostgreSQL document-table link repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.document_table_link import DocumentTableLink, TableLinkType
from app.infrastructure.database.models.document_table_link import DocumentTableLinkModel


class PostgresDocumentTableLinkRepository:
    """PostgreSQL implementation of DocumentTableLinkRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, link_id: UUID) -> DocumentTableLink | None:
        """Get link by ID."""
        stmt = select(DocumentTableLinkModel).where(
            DocumentTableLinkModel.id == link_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, link: DocumentTableLink) -> DocumentTableLink:
        """Create a new link."""
        model = self._to_model(link)
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def create_many(
        self, links: list[DocumentTableLink]
    ) -> list[DocumentTableLink]:
        """Create multiple links."""
        models = [self._to_model(link) for link in links]
        self.session.add_all(models)
        await self.session.flush()
        return [self._to_entity(m) for m in models]

    async def delete(self, link_id: UUID) -> None:
        """Delete a link."""
        stmt = select(DocumentTableLinkModel).where(
            DocumentTableLinkModel.id == link_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete all links from a document. Returns count deleted."""
        stmt = select(DocumentTableLinkModel).where(
            DocumentTableLinkModel.document_id == document_id
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        count = len(models)
        for model in models:
            await self.session.delete(model)
        await self.session.flush()
        return count

    async def get_by_document(self, document_id: UUID) -> list[DocumentTableLink]:
        """Get all table links from a document."""
        stmt = (
            select(DocumentTableLinkModel)
            .where(DocumentTableLinkModel.document_id == document_id)
            .order_by(DocumentTableLinkModel.position_start)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_by_table(self, table_id: UUID) -> list[DocumentTableLink]:
        """Get all document links to a table."""
        stmt = (
            select(DocumentTableLinkModel)
            .where(DocumentTableLinkModel.table_id == table_id)
            .order_by(DocumentTableLinkModel.created_at)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_by_row(self, row_id: UUID) -> list[DocumentTableLink]:
        """Get all document links to a specific row."""
        stmt = (
            select(DocumentTableLinkModel)
            .where(DocumentTableLinkModel.row_id == row_id)
            .order_by(DocumentTableLinkModel.created_at)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_table_links_only(self, document_id: UUID) -> list[DocumentTableLink]:
        """Get only table links (not row links) from a document."""
        stmt = (
            select(DocumentTableLinkModel)
            .where(
                DocumentTableLinkModel.document_id == document_id,
                DocumentTableLinkModel.link_type == TableLinkType.TABLE.value,
            )
            .order_by(DocumentTableLinkModel.position_start)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_row_links_only(self, document_id: UUID) -> list[DocumentTableLink]:
        """Get only row links (not table links) from a document."""
        stmt = (
            select(DocumentTableLinkModel)
            .where(
                DocumentTableLinkModel.document_id == document_id,
                DocumentTableLinkModel.link_type == TableLinkType.TABLE_ROW.value,
            )
            .order_by(DocumentTableLinkModel.position_start)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: DocumentTableLinkModel) -> DocumentTableLink:
        """Convert model to entity."""
        return DocumentTableLink(
            id=model.id,
            vault_id=model.vault_id,
            document_id=model.document_id,
            table_id=model.table_id,
            row_id=model.row_id,
            link_type=TableLinkType(model.link_type),
            link_text=model.link_text,
            position_start=model.position_start,
            created_at=model.created_at,
        )

    def _to_model(self, entity: DocumentTableLink) -> DocumentTableLinkModel:
        """Convert entity to model."""
        return DocumentTableLinkModel(
            id=entity.id,
            vault_id=entity.vault_id,
            document_id=entity.document_id,
            table_id=entity.table_id,
            row_id=entity.row_id,
            link_type=entity.link_type.value,
            link_text=entity.link_text,
            position_start=entity.position_start,
            created_at=entity.created_at,
        )
