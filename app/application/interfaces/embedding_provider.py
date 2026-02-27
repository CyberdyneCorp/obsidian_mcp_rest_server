"""Embedding provider port interface."""

from typing import Protocol


class EmbeddingProvider(Protocol):
    """Port interface for generating text embeddings."""

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        ...

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        ...

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Token count
        """
        ...

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> list[tuple[str, int]]:
        """Split text into chunks for embedding.

        Args:
            text: Text to chunk
            chunk_size: Target chunk size in tokens
            overlap: Token overlap between chunks

        Returns:
            List of (chunk_text, token_count) tuples
        """
        ...
