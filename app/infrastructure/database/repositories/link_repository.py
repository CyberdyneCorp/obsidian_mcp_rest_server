"""PostgreSQL document link repository implementation."""
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.document_link import DocumentLink, LinkType
from app.infrastructure.database.models.document_link import DocumentLinkModel
from app.infrastructure.database.repositories.base import BaseRepository


class PostgresDocumentLinkRepository(BaseRepository[DocumentLink, DocumentLinkModel]):
    """PostgreSQL implementation of DocumentLinkRepository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    def _get_model_class(self) -> type[DocumentLinkModel]:
        return DocumentLinkModel

    async def create_many(self, links: list[DocumentLink]) -> list[DocumentLink]:
        """Create multiple links."""
        models = [self._to_model(link) for link in links]
        self.session.add_all(models)
        await self.session.flush()
        self._logger.info(f"Created {len(models)} document links")
        return [self._to_entity(m) for m in models]

    async def delete_by_source(self, source_document_id: UUID) -> int:
        """Delete all links from a source document."""
        stmt = delete(DocumentLinkModel).where(
            DocumentLinkModel.source_document_id == source_document_id
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        count = int(getattr(result, "rowcount", 0) or 0)
        self._logger.info(f"Deleted {count} outgoing links from document={source_document_id}")
        return count

    async def get_outgoing_links(self, document_id: UUID) -> list[DocumentLink]:
        """Get all outgoing links from a document."""
        stmt = (
            select(DocumentLinkModel)
            .where(DocumentLinkModel.source_document_id == document_id)
            .order_by(DocumentLinkModel.position_start)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        self._logger.debug(f"Found {len(models)} outgoing links from document={document_id}")
        return [self._to_entity(m) for m in models]

    async def get_incoming_links(self, document_id: UUID) -> list[DocumentLink]:
        """Get all incoming links to a document (backlinks)."""
        stmt = select(DocumentLinkModel).where(
            DocumentLinkModel.target_document_id == document_id
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        self._logger.debug(f"Found {len(models)} incoming links to document={document_id}")
        return [self._to_entity(m) for m in models]

    async def get_unresolved_links(self, vault_id: UUID) -> list[DocumentLink]:
        """Get all unresolved links in a vault."""
        stmt = select(DocumentLinkModel).where(
            DocumentLinkModel.vault_id == vault_id,
            DocumentLinkModel.is_resolved == False,  # noqa: E712
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        self._logger.debug(f"Found {len(models)} unresolved links in vault={vault_id}")
        return [self._to_entity(m) for m in models]

    async def count_outgoing(self, document_id: UUID) -> int:
        """Count outgoing links from a document."""
        stmt = (
            select(func.count())
            .select_from(DocumentLinkModel)
            .where(DocumentLinkModel.source_document_id == document_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def count_incoming(self, document_id: UUID) -> int:
        """Count incoming links to a document."""
        stmt = (
            select(func.count())
            .select_from(DocumentLinkModel)
            .where(DocumentLinkModel.target_document_id == document_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update_resolved(
        self,
        resolved_links: list[tuple[UUID, UUID]],
    ) -> int:
        """Bulk update links with resolved target document IDs."""
        if not resolved_links:
            return 0

        updated = 0
        for link_id, target_document_id in resolved_links:
            stmt = (
                update(DocumentLinkModel)
                .where(DocumentLinkModel.id == link_id)
                .values(
                    target_document_id=target_document_id,
                    is_resolved=True,
                )
            )
            result = await self.session.execute(stmt)
            updated += int(getattr(result, "rowcount", 0) or 0)

        await self.session.flush()
        self._logger.info(f"Resolved {updated} document links")
        return updated

    def _to_entity(self, model: DocumentLinkModel) -> DocumentLink:
        """Convert model to entity."""
        return DocumentLink(
            id=model.id,
            vault_id=model.vault_id,
            source_document_id=model.source_document_id,
            target_document_id=model.target_document_id,
            link_text=model.link_text,
            display_text=model.display_text,
            link_type=LinkType(model.link_type),
            is_resolved=model.is_resolved,
            position_start=model.position_start,
            created_at=model.created_at,
        )

    def _to_model(self, entity: DocumentLink) -> DocumentLinkModel:
        """Convert entity to model."""
        return DocumentLinkModel(
            id=entity.id,
            vault_id=entity.vault_id,
            source_document_id=entity.source_document_id,
            target_document_id=entity.target_document_id,
            link_text=entity.link_text,
            display_text=entity.display_text,
            link_type=entity.link_type.value if hasattr(entity.link_type, 'value') else entity.link_type,
            is_resolved=entity.is_resolved,
            position_start=entity.position_start,
            created_at=entity.created_at,
        )
