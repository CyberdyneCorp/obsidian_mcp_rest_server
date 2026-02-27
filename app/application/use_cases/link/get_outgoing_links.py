"""Get outgoing links use case."""

from uuid import UUID

from app.application.dto.link_dto import LinkDTO
from app.application.interfaces.repositories import (
    DocumentLinkRepository,
    DocumentRepository,
    VaultRepository,
)
from app.domain.exceptions import DocumentNotFoundError, VaultNotFoundError


class GetOutgoingLinksUseCase:
    """Use case for getting outgoing links from a document."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        document_repo: DocumentRepository,
        link_repo: DocumentLinkRepository,
    ) -> None:
        self.vault_repo = vault_repo
        self.document_repo = document_repo
        self.link_repo = link_repo

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        document_id: UUID,
    ) -> list[LinkDTO]:
        """Get outgoing links from a document.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            document_id: Document UUID

        Returns:
            List of link DTOs

        Raises:
            VaultNotFoundError: If vault not found
            DocumentNotFoundError: If document not found
        """
        # Get vault
        vault = await self.vault_repo.get_by_slug(user_id, vault_slug)
        if not vault:
            raise VaultNotFoundError(slug=vault_slug)

        # Get document
        document = await self.document_repo.get_by_id(document_id)
        if not document or document.vault_id != vault.id:
            raise DocumentNotFoundError(document_id=str(document_id))

        # Get outgoing links
        links = await self.link_repo.get_outgoing_links(document_id)

        # Build link DTOs
        link_dtos = []
        for link in links:
            target_title = None
            target_path = None

            if link.is_resolved and link.target_document_id:
                target_doc = await self.document_repo.get_by_id(link.target_document_id)
                if target_doc:
                    target_title = target_doc.title
                    target_path = target_doc.path

            link_dtos.append(
                LinkDTO.from_entity(
                    link=link,
                    target_title=target_title,
                    target_path=target_path,
                )
            )

        return link_dtos
