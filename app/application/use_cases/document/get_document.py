"""Get document use case."""

import logging
from uuid import UUID

from app.application.dto.document_dto import DocumentDTO
from app.application.interfaces.repositories import DocumentRepository, VaultRepository
from app.application.use_cases.base import VaultAccessMixin
from app.domain.exceptions import DocumentNotFoundError


class GetDocumentUseCase(VaultAccessMixin):
    """Use case for getting a document."""

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
        document_id: UUID | None = None,
        path: str | None = None,
    ) -> DocumentDTO:
        """Get a document by ID or path.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            document_id: Document UUID (optional)
            path: Document path (optional)

        Returns:
            Document DTO

        Raises:
            VaultNotFoundError: If vault not found
            DocumentNotFoundError: If document not found
            ValueError: If neither document_id nor path provided
        """
        if not document_id and not path:
            raise ValueError("Either document_id or path must be provided")

        vault = await self.get_vault_or_raise(user_id, vault_slug)

        # Get document
        if document_id:
            document = await self.document_repo.get_by_id(document_id)
            if not document or document.vault_id != vault.id:
                raise DocumentNotFoundError(document_id=str(document_id))
            self._logger.debug(f"Retrieved document id={document_id}")
        else:
            document = await self.document_repo.get_by_path(vault.id, path)  # type: ignore
            if not document:
                raise DocumentNotFoundError(path=path)
            self._logger.debug(f"Retrieved document path={path}")

        return DocumentDTO.from_entity(document)
