"""Create document use case."""

from uuid import UUID

from app.application.dto.document_dto import DocumentCreateDTO, DocumentDTO
from app.application.interfaces.repositories import (
    DocumentRepository,
    FolderRepository,
    VaultRepository,
)
from app.domain.entities.document import Document
from app.domain.exceptions import DuplicateDocumentError, VaultNotFoundError
from app.domain.services.markdown_processor import MarkdownProcessor
from app.domain.value_objects.document_path import DocumentPath
from app.domain.value_objects.frontmatter import Frontmatter


class CreateDocumentUseCase:
    """Use case for creating a new document."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        document_repo: DocumentRepository,
        folder_repo: FolderRepository,
    ) -> None:
        self.vault_repo = vault_repo
        self.document_repo = document_repo
        self.folder_repo = folder_repo
        self.markdown_processor = MarkdownProcessor()

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        data: DocumentCreateDTO,
    ) -> DocumentDTO:
        """Create a new document.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            data: Document creation data

        Returns:
            Created document DTO

        Raises:
            VaultNotFoundError: If vault not found
            DuplicateDocumentError: If document path already exists
        """
        # Get vault
        vault = await self.vault_repo.get_by_slug(user_id, vault_slug)
        if not vault:
            raise VaultNotFoundError(slug=vault_slug)

        # Check for duplicate
        existing = await self.document_repo.get_by_path(vault.id, data.path)
        if existing:
            raise DuplicateDocumentError(data.path)

        # Parse content
        parsed = self.markdown_processor.parse(data.content)

        # Merge frontmatter
        frontmatter = parsed.frontmatter
        if data.frontmatter:
            provided_fm = Frontmatter.from_dict(data.frontmatter)
            frontmatter = frontmatter.merge(provided_fm)

        # Get or create folder
        doc_path = DocumentPath(data.path)
        folder_id = None
        if doc_path.folder_path:
            folder = await self.folder_repo.get_or_create_path(
                vault.id,
                doc_path.folder_path,
            )
            folder_id = folder.id

        # Create document
        document = Document.create(
            vault_id=vault.id,
            path=data.path,
            content=parsed.content,
            frontmatter=frontmatter,
            folder_id=folder_id,
        )
        document.set_link_count(len(parsed.links))

        document = await self.document_repo.create(document)

        # Update vault document count
        vault.increment_document_count()
        await self.vault_repo.update(vault)

        return DocumentDTO.from_entity(document)
