"""List documents use case."""

import logging
from uuid import UUID

from app.application.dto.document_dto import DocumentSummaryDTO
from app.application.interfaces.repositories import DocumentRepository, VaultRepository
from app.application.use_cases.base import VaultAccessMixin


class ListDocumentsUseCase(VaultAccessMixin):
    """Use case for listing documents in a vault."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        document_repo: DocumentRepository,
    ) -> None:
        self.vault_repo = vault_repo
        self.document_repo = document_repo
        self._logger = logging.getLogger(__name__)

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        limit: int = 50,
        offset: int = 0,
        folder: str | None = None,
        tag: str | None = None,
    ) -> tuple[list[DocumentSummaryDTO], int]:
        """List documents in a vault.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            limit: Maximum results
            offset: Pagination offset
            folder: Optional folder filter
            tag: Optional tag filter

        Returns:
            Tuple of (documents, total_count)

        Raises:
            VaultNotFoundError: If vault not found
        """
        _ = tag
        vault = await self.get_vault_or_raise(user_id, vault_slug)

        # Get documents
        documents = await self.document_repo.list_by_vault(
            vault.id,
            limit=limit,
            offset=offset,
        )

        # Filter by folder if specified
        if folder:
            documents = [d for d in documents if d.path.startswith(folder + "/")]

        # Get total count
        total = await self.document_repo.count_by_vault(vault.id)
        self._logger.debug(f"Listed {len(documents)} documents from vault={vault_slug}")

        return (
            [DocumentSummaryDTO.from_entity(d) for d in documents],
            total,
        )
