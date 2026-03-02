"""Delete document use case."""

import logging
from uuid import UUID

from app.application.interfaces.graph_provider import GraphProvider
from app.application.interfaces.repositories import (
    DocumentLinkRepository,
    DocumentRepository,
    EmbeddingChunkRepository,
    VaultRepository,
)
from app.application.use_cases.base import VaultAccessMixin
from app.domain.exceptions import DocumentNotFoundError


class DeleteDocumentUseCase(VaultAccessMixin):
    """Use case for deleting a document."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        document_repo: DocumentRepository,
        link_repo: DocumentLinkRepository,
        embedding_repo: EmbeddingChunkRepository | None = None,
        graph_provider: GraphProvider | None = None,
    ) -> None:
        self.vault_repo = vault_repo
        self.document_repo = document_repo
        self.link_repo = link_repo
        self.embedding_repo = embedding_repo
        self.graph_provider = graph_provider
        self._logger = logging.getLogger(__name__)

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        document_id: UUID,
    ) -> None:
        """Delete a document.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            document_id: Document UUID

        Raises:
            VaultNotFoundError: If vault not found
            DocumentNotFoundError: If document not found
        """
        vault = await self.get_vault_or_raise(user_id, vault_slug)

        # Get document
        document = await self.document_repo.get_by_id(document_id)
        if not document or document.vault_id != vault.id:
            raise DocumentNotFoundError(document_id=str(document_id))

        # Delete embedding chunks
        if self.embedding_repo:
            await self.embedding_repo.delete_by_document(document_id)

        # Delete links
        await self.link_repo.delete_by_source(document_id)

        # Delete from graph
        if self.graph_provider:
            await self.graph_provider.delete_document_node(document_id)

        # Delete document
        await self.document_repo.delete(document_id)

        # Update vault document count
        vault.decrement_document_count()
        await self.vault_repo.update(vault)
        self._logger.info(f"Deleted document id={document_id} from vault={vault_slug}")
