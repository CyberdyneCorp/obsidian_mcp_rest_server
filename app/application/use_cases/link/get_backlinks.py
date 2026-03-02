"""Get backlinks use case."""

import logging
from uuid import UUID

from app.application.dto.link_dto import BacklinkDTO
from app.application.interfaces.repositories import (
    DocumentLinkRepository,
    DocumentRepository,
    VaultRepository,
)
from app.application.use_cases.base import VaultAccessMixin
from app.domain.exceptions import DocumentNotFoundError


class GetBacklinksUseCase(VaultAccessMixin):
    """Use case for getting backlinks to a document."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        document_repo: DocumentRepository,
        link_repo: DocumentLinkRepository,
    ) -> None:
        self.vault_repo = vault_repo
        self.document_repo = document_repo
        self.link_repo = link_repo
        self._logger = logging.getLogger(__name__)

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        document_id: UUID,
    ) -> list[BacklinkDTO]:
        """Get backlinks to a document.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            document_id: Document UUID

        Returns:
            List of backlink DTOs

        Raises:
            VaultNotFoundError: If vault not found
            DocumentNotFoundError: If document not found
        """
        vault = await self.get_vault_or_raise(user_id, vault_slug)

        # Get document
        document = await self.document_repo.get_by_id(document_id)
        if not document or document.vault_id != vault.id:
            raise DocumentNotFoundError(document_id=str(document_id))

        # Get incoming links
        links = await self.link_repo.get_incoming_links(document_id)

        # Build backlink DTOs
        backlinks = []
        for link in links:
            # Get source document
            source_doc = await self.document_repo.get_by_id(link.source_document_id)
            if source_doc:
                backlinks.append(
                    BacklinkDTO.from_link(
                        link=link,
                        source_title=source_doc.title,
                        source_path=source_doc.path,
                        context=None,  # TODO: Extract context from content
                    )
                )

        self._logger.debug(f"Found {len(backlinks)} backlinks to document={document_id}")
        return backlinks
