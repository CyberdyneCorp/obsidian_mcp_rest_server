"""Export vault use case."""

import io
import logging
import zipfile
from uuid import UUID

from app.application.interfaces.repositories import (
    DocumentRepository,
    FolderRepository,
    VaultRepository,
)
from app.application.use_cases.base import VaultAccessMixin
from app.domain.services.markdown_processor import MarkdownProcessor


class ExportVaultUseCase(VaultAccessMixin):
    """Use case for exporting a vault as a ZIP file."""

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
        self._logger = logging.getLogger(__name__)

    async def execute(self, user_id: UUID, slug: str) -> bytes:
        """Export a vault as a ZIP file.

        Args:
            user_id: User ID
            slug: Vault slug

        Returns:
            ZIP file content as bytes

        Raises:
            VaultNotFoundError: If vault not found
        """
        vault = await self.get_vault_or_raise(user_id, slug)

        # Get all documents
        documents = await self.document_repo.list_by_vault(vault.id, limit=10000)

        # Create ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for doc in documents:
                # Render document with frontmatter
                content = self.markdown_processor.render_with_frontmatter(
                    doc.content,
                    doc.frontmatter,
                )

                # Add to ZIP
                zf.writestr(doc.path, content.encode("utf-8"))

        self._logger.info(f"Exported vault slug={slug} with {len(documents)} documents")
        return zip_buffer.getvalue()
