"""Get document use case."""

from uuid import UUID

from app.application.dto.document_dto import DocumentDTO
from app.application.interfaces.repositories import DocumentRepository, VaultRepository
from app.domain.exceptions import DocumentNotFoundError, VaultNotFoundError


class GetDocumentUseCase:
    """Use case for getting a document."""

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

        # Get vault
        vault = await self.vault_repo.get_by_slug(user_id, vault_slug)
        if not vault:
            raise VaultNotFoundError(slug=vault_slug)

        # Get document
        if document_id:
            document = await self.document_repo.get_by_id(document_id)
            if not document or document.vault_id != vault.id:
                raise DocumentNotFoundError(document_id=str(document_id))
        else:
            document = await self.document_repo.get_by_path(vault.id, path)  # type: ignore
            if not document:
                raise DocumentNotFoundError(path=path)

        return DocumentDTO.from_entity(document)
