"""OpenAI embedding adapter."""

import logging

import tiktoken
from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenAIEmbeddingAdapter:
    """OpenAI embedding provider implementation."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.openai_api_key
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = settings.embedding_model
        self.encoding = tiktoken.encoding_for_model(self.model)

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return list(response.data[0].embedding)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        # OpenAI allows batch embedding
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )

        # Sort by index to maintain order
        embeddings = sorted(response.data, key=lambda x: x.index)
        return [list(e.embedding) for e in embeddings]

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

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
        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)

        if total_tokens <= chunk_size:
            return [(text, total_tokens)]

        chunks = []
        start = 0

        while start < total_tokens:
            # Get chunk tokens
            end = min(start + chunk_size, total_tokens)
            chunk_tokens = tokens[start:end]

            # Decode back to text
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append((chunk_text, len(chunk_tokens)))

            # Move start with overlap
            start = end - overlap if end < total_tokens else total_tokens

        return chunks
