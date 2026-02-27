"""Fulltext search use case."""

from uuid import UUID

from app.application.dto.document_dto import DocumentSummaryDTO
from app.application.dto.search_dto import FulltextSearchResultDTO
from app.application.interfaces.repositories import DocumentRepository, VaultRepository
from app.domain.exceptions import VaultNotFoundError


class FulltextSearchUseCase:
    """Use case for full-text search."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        document_repo: DocumentRepository,
    ) -> None:
        self.vault_repo = vault_repo
        self.document_repo = document_repo

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        query: str,
        limit: int = 20,
        folder: str | None = None,
    ) -> list[FulltextSearchResultDTO]:
        """Perform full-text search.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            query: Search query
            limit: Maximum results
            folder: Optional folder filter

        Returns:
            List of search results

        Raises:
            VaultNotFoundError: If vault not found
        """
        # Get vault
        vault = await self.vault_repo.get_by_slug(user_id, vault_slug)
        if not vault:
            raise VaultNotFoundError(slug=vault_slug)

        # Search documents
        documents = await self.document_repo.search_fulltext(
            vault_id=vault.id,
            query=query,
            limit=limit,
        )

        # Build results
        results = []
        for doc in documents:
            # Apply folder filter
            if folder and not doc.path.startswith(folder + "/"):
                continue

            # Generate headline (simple excerpt around match)
            headline = self._generate_headline(doc.content, query)

            results.append(
                FulltextSearchResultDTO(
                    document=DocumentSummaryDTO.from_entity(doc),
                    headline=headline,
                )
            )

        return results

    def _generate_headline(
        self,
        content: str,
        query: str,
        context_chars: int = 100,
    ) -> str | None:
        """Generate a headline with search terms highlighted."""
        query_lower = query.lower()
        content_lower = content.lower()

        pos = content_lower.find(query_lower)
        if pos == -1:
            # Try individual words
            words = query.split()
            for word in words:
                pos = content_lower.find(word.lower())
                if pos != -1:
                    break

        if pos == -1:
            return None

        # Extract context around match
        start = max(0, pos - context_chars)
        end = min(len(content), pos + len(query) + context_chars)

        excerpt = content[start:end]

        # Add ellipsis if truncated
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."

        return excerpt
