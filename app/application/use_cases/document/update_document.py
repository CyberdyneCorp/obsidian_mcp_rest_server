"""Update document use case."""

import logging
from uuid import UUID

from app.application.dto.document_dto import DocumentDTO, DocumentUpdateDTO
from app.application.interfaces.repositories import (
    DocumentLinkRepository,
    DocumentRepository,
    VaultRepository,
)
from app.application.use_cases.base import VaultAccessMixin
from app.domain.exceptions import DocumentNotFoundError
from app.domain.services.markdown_processor import MarkdownProcessor
from app.domain.value_objects.frontmatter import Frontmatter


class UpdateDocumentUseCase(VaultAccessMixin):
    """Use case for updating a document."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        document_repo: DocumentRepository,
        link_repo: DocumentLinkRepository,
    ) -> None:
        self.vault_repo = vault_repo
        self.document_repo = document_repo
        self.link_repo = link_repo
        self.markdown_processor = MarkdownProcessor()
        self._logger = logging.getLogger(__name__)

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        document_id: UUID,
        data: DocumentUpdateDTO,
    ) -> DocumentDTO:
        """Update a document.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            document_id: Document UUID
            data: Update data

        Returns:
            Updated document DTO

        Raises:
            VaultNotFoundError: If vault not found
            DocumentNotFoundError: If document not found
        """
        vault = await self.get_vault_or_raise(user_id, vault_slug)

        # Get document
        document = await self.document_repo.get_by_id(document_id)
        if not document or document.vault_id != vault.id:
            raise DocumentNotFoundError(document_id=str(document_id))

        # Update content if provided
        if data.content is not None:
            document.update_content(data.content)

            # Re-parse for links
            parsed = self.markdown_processor.parse(data.content)
            document.set_link_count(len(parsed.links))

            # TODO: Update links in database

        # Update frontmatter if provided
        if data.frontmatter is not None:
            new_frontmatter = Frontmatter.from_dict(data.frontmatter)
            document.update_frontmatter(new_frontmatter)

        # Save document
        document = await self.document_repo.update(document)
        self._logger.info(f"Updated document id={document_id}")

        return DocumentDTO.from_entity(document)
