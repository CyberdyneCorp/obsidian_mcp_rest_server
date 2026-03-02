"""EmbeddingChunk entity for document embeddings."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


def _utcnow_naive() -> datetime:
    """Return UTC timestamp as naive datetime for TIMESTAMP WITHOUT TIME ZONE."""
    return datetime.now(UTC).replace(tzinfo=None)


@dataclass
class EmbeddingChunk:
    """EmbeddingChunk entity representing a chunk of document with its embedding.

    Documents are split into chunks for embedding, enabling more precise
    semantic search results.
    """

    id: UUID = field(default_factory=uuid4)
    vault_id: UUID = field(default_factory=uuid4)
    document_id: UUID = field(default_factory=uuid4)
    chunk_index: int = 0  # Position within the document
    content: str = ""  # Chunk text
    token_count: int = 0  # Number of tokens
    embedding: list[float] = field(default_factory=list)  # Vector (1536 dims)
    created_at: datetime = field(default_factory=_utcnow_naive)

    def set_embedding(self, embedding: list[float]) -> None:
        """Set the embedding vector."""
        self.embedding = embedding

    def has_embedding(self) -> bool:
        """Check if this chunk has an embedding."""
        return len(self.embedding) > 0

    @classmethod
    def create(
        cls,
        vault_id: UUID,
        document_id: UUID,
        chunk_index: int,
        content: str,
        token_count: int,
        embedding: list[float] | None = None,
    ) -> "EmbeddingChunk":
        """Factory method to create a new embedding chunk."""
        return cls(
            vault_id=vault_id,
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            token_count=token_count,
            embedding=embedding or [],
        )
