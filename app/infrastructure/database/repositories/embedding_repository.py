"""PostgreSQL embedding chunk repository implementation."""

import logging
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.embedding_chunk import EmbeddingChunk
from app.infrastructure.database.models.embedding_chunk import EmbeddingChunkModel

logger = logging.getLogger(__name__)


class PostgresEmbeddingChunkRepository:
    """PostgreSQL implementation of EmbeddingChunkRepository.

    Note: This repository doesn't extend BaseRepository because it doesn't
    have standard CRUD operations (no get_by_id, update, etc.).
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, chunk: EmbeddingChunk) -> EmbeddingChunk:
        """Create a new embedding chunk."""
        model = self._to_model(chunk)
        self.session.add(model)
        await self.session.flush()
        logger.info(f"Created embedding chunk for document={chunk.document_id}")
        return self._to_entity(model)

    async def create_many(self, chunks: list[EmbeddingChunk]) -> list[EmbeddingChunk]:
        """Create multiple embedding chunks."""
        models = [self._to_model(c) for c in chunks]
        self.session.add_all(models)
        await self.session.flush()
        logger.info(f"Created {len(models)} embedding chunks")
        return [self._to_entity(m) for m in models]

    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete all chunks for a document."""
        stmt = delete(EmbeddingChunkModel).where(
            EmbeddingChunkModel.document_id == document_id
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        count = int(getattr(result, "rowcount", 0) or 0)
        logger.info(f"Deleted {count} embedding chunks for document={document_id}")
        return count

    async def get_by_document(self, document_id: UUID) -> list[EmbeddingChunk]:
        """Get all chunks for a document."""
        stmt = (
            select(EmbeddingChunkModel)
            .where(EmbeddingChunkModel.document_id == document_id)
            .order_by(EmbeddingChunkModel.chunk_index)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        logger.debug(f"Found {len(models)} embedding chunks for document={document_id}")
        return [self._to_entity(m) for m in models]

    async def search_similar(
        self,
        vault_id: UUID,
        embedding: list[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> list[tuple[EmbeddingChunk, float]]:
        """Search for similar chunks using cosine similarity."""
        stmt = (
            select(
                EmbeddingChunkModel,
                (1 - EmbeddingChunkModel.embedding.cosine_distance(embedding)).label("similarity"),
            )
            .where(EmbeddingChunkModel.vault_id == vault_id)
            .where((1 - EmbeddingChunkModel.embedding.cosine_distance(embedding)) >= threshold)
            .order_by(EmbeddingChunkModel.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        logger.debug(f"Similarity search found {len(rows)} chunks in vault={vault_id}")
        return [(self._to_entity(row[0]), float(row[1])) for row in rows]

    def _to_entity(self, model: EmbeddingChunkModel) -> EmbeddingChunk:
        """Convert model to entity."""
        return EmbeddingChunk(
            id=model.id,
            vault_id=model.vault_id,
            document_id=model.document_id,
            chunk_index=model.chunk_index,
            content=model.content,
            token_count=model.token_count,
            embedding=list(model.embedding) if model.embedding is not None else [],
            created_at=model.created_at,
        )

    def _to_model(self, entity: EmbeddingChunk) -> EmbeddingChunkModel:
        """Convert entity to model."""
        return EmbeddingChunkModel(
            id=entity.id,
            vault_id=entity.vault_id,
            document_id=entity.document_id,
            chunk_index=entity.chunk_index,
            content=entity.content,
            token_count=entity.token_count,
            embedding=entity.embedding,
            created_at=entity.created_at,
        )
