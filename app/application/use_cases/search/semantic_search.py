"""Semantic search use case."""

import logging
from uuid import UUID

from app.application.dto.document_dto import DocumentSummaryDTO
from app.application.dto.search_dto import SearchQueryDTO, SearchResultDTO
from app.application.interfaces.repositories import (
    DocumentRepository,
    EmbeddingChunkRepository,
    VaultRepository,
)
from app.application.interfaces.embedding_provider import EmbeddingProvider
from app.application.use_cases.base import VaultAccessMixin
from app.domain.exceptions import EmbeddingServiceError


class SemanticSearchUseCase(VaultAccessMixin):
    """Use case for semantic (vector) search."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        document_repo: DocumentRepository,
        embedding_repo: EmbeddingChunkRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.vault_repo = vault_repo
        self.document_repo = document_repo
        self.embedding_repo = embedding_repo
        self.embedding_provider = embedding_provider
        self._logger = logging.getLogger(__name__)

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        query: SearchQueryDTO,
    ) -> list[SearchResultDTO]:
        """Perform semantic search.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            query: Search query parameters

        Returns:
            List of search results

        Raises:
            VaultNotFoundError: If vault not found
            EmbeddingServiceError: If embedding generation fails
        """
        vault = await self.get_vault_or_raise(user_id, vault_slug)

        try:
            # Generate query embedding
            query_embedding = await self.embedding_provider.embed_text(query.query)
        except Exception as e:
            raise EmbeddingServiceError(str(e)) from e

        # Search similar chunks
        results = await self.embedding_repo.search_similar(
            vault_id=vault.id,
            embedding=query_embedding,
            limit=query.limit * 2,  # Get more to allow filtering
            threshold=query.threshold,
        )

        # Group by document and get best score per document
        doc_scores: dict[UUID, tuple[float, str]] = {}
        for chunk, score in results:
            if chunk.document_id not in doc_scores:
                doc_scores[chunk.document_id] = (score, chunk.content)
            elif score > doc_scores[chunk.document_id][0]:
                doc_scores[chunk.document_id] = (score, chunk.content)

        # Build results
        search_results = []
        for doc_id, (score, matched_chunk) in sorted(
            doc_scores.items(),
            key=lambda x: x[1][0],
            reverse=True,
        )[: query.limit]:
            document = await self.document_repo.get_by_id(doc_id)
            if not document:
                continue

            # Apply folder filter
            if query.folder and not document.path.startswith(query.folder + "/"):
                continue

            # Apply tag filter
            if query.tags:
                doc_tags = set(document.frontmatter.tags)
                if not any(t in doc_tags for t in query.tags):
                    continue

            search_results.append(
                SearchResultDTO(
                    document=DocumentSummaryDTO.from_entity(document),
                    score=score,
                    matched_chunk=matched_chunk[:500],  # Truncate
                )
            )

        self._logger.debug(f"Semantic search returned {len(search_results)} results for query in vault={vault_slug}")
        return search_results
