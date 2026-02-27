"""Sync links use case."""

from uuid import UUID

from app.application.interfaces.repositories import (
    DocumentLinkRepository,
    DocumentRepository,
    VaultRepository,
)
from app.domain.entities.document_link import DocumentLink, LinkType
from app.domain.exceptions import DocumentNotFoundError, VaultNotFoundError
from app.domain.services.link_resolver import LinkResolver
from app.domain.services.markdown_processor import MarkdownProcessor


class SyncLinksUseCase:
    """Use case for syncing links after document update."""

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
        self.link_resolver = LinkResolver()

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        document_id: UUID,
    ) -> int:
        """Sync links for a document.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            document_id: Document UUID

        Returns:
            Number of links created

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

        # Delete existing links from this document
        await self.link_repo.delete_by_source(document_id)

        # Parse document for links
        links_with_positions = self.markdown_processor.extract_links_with_positions(
            document.content
        )

        if not links_with_positions:
            document.set_link_count(0)
            await self.document_repo.update(document)
            return 0

        # Get all documents for resolution
        all_documents = await self.document_repo.list_by_vault(vault.id, limit=10000)

        # Create new links
        new_links = []
        for wiki_link, position in links_with_positions:
            link_type = LinkType.EMBED if wiki_link.is_embed else LinkType.WIKILINK
            if wiki_link.heading:
                link_type = LinkType.HEADER
            elif wiki_link.block_id:
                link_type = LinkType.BLOCK

            # Resolve target
            target_doc = self.link_resolver.resolve(wiki_link, all_documents)

            link = DocumentLink.create(
                vault_id=vault.id,
                source_document_id=document_id,
                link_text=wiki_link.target,
                display_text=wiki_link.display_text,
                link_type=link_type,
                position_start=position,
                target_document_id=target_doc.id if target_doc else None,
            )
            new_links.append(link)

        if new_links:
            await self.link_repo.create_many(new_links)

        # Update document link count
        document.set_link_count(len(new_links))
        await self.document_repo.update(document)

        return len(new_links)
