"""Repository port interfaces."""

from abc import ABC, abstractmethod
from typing import Protocol
from uuid import UUID

from app.domain.entities.document import Document
from app.domain.entities.document_link import DocumentLink
from app.domain.entities.embedding_chunk import EmbeddingChunk
from app.domain.entities.folder import Folder
from app.domain.entities.tag import Tag
from app.domain.entities.user import User
from app.domain.entities.vault import Vault


class UserRepository(Protocol):
    """Port interface for user persistence."""

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        ...

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        ...

    async def create(self, user: User) -> User:
        """Create a new user."""
        ...

    async def update(self, user: User) -> User:
        """Update an existing user."""
        ...

    async def delete(self, user_id: UUID) -> None:
        """Delete a user."""
        ...


class VaultRepository(Protocol):
    """Port interface for vault persistence."""

    async def get_by_id(self, vault_id: UUID) -> Vault | None:
        """Get vault by ID."""
        ...

    async def get_by_slug(self, user_id: UUID, slug: str) -> Vault | None:
        """Get vault by user ID and slug."""
        ...

    async def create(self, vault: Vault) -> Vault:
        """Create a new vault."""
        ...

    async def update(self, vault: Vault) -> Vault:
        """Update an existing vault."""
        ...

    async def delete(self, vault_id: UUID) -> None:
        """Delete a vault and all its contents."""
        ...

    async def list_by_user(self, user_id: UUID) -> list[Vault]:
        """List all vaults for a user."""
        ...


class FolderRepository(Protocol):
    """Port interface for folder persistence."""

    async def get_by_id(self, folder_id: UUID) -> Folder | None:
        """Get folder by ID."""
        ...

    async def get_by_path(self, vault_id: UUID, path: str) -> Folder | None:
        """Get folder by vault ID and path."""
        ...

    async def create(self, folder: Folder) -> Folder:
        """Create a new folder."""
        ...

    async def create_many(self, folders: list[Folder]) -> list[Folder]:
        """Create multiple folders."""
        ...

    async def delete(self, folder_id: UUID) -> None:
        """Delete a folder."""
        ...

    async def list_by_vault(self, vault_id: UUID) -> list[Folder]:
        """List all folders in a vault."""
        ...

    async def get_or_create_path(
        self,
        vault_id: UUID,
        path: str,
    ) -> Folder:
        """Get or create a folder at the given path (including parents)."""
        ...


class DocumentRepository(Protocol):
    """Port interface for document persistence."""

    async def get_by_id(self, document_id: UUID) -> Document | None:
        """Get document by ID."""
        ...

    async def get_by_path(self, vault_id: UUID, path: str) -> Document | None:
        """Get document by vault ID and path."""
        ...

    async def create(self, document: Document) -> Document:
        """Create a new document."""
        ...

    async def create_many(self, documents: list[Document]) -> list[Document]:
        """Create multiple documents."""
        ...

    async def update(self, document: Document) -> Document:
        """Update an existing document."""
        ...

    async def delete(self, document_id: UUID) -> None:
        """Delete a document."""
        ...

    async def list_by_vault(
        self,
        vault_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        """List documents in a vault with pagination."""
        ...

    async def list_by_folder(self, folder_id: UUID) -> list[Document]:
        """List documents in a specific folder."""
        ...

    async def count_by_vault(self, vault_id: UUID) -> int:
        """Count documents in a vault."""
        ...

    async def search_fulltext(
        self,
        vault_id: UUID,
        query: str,
        limit: int = 20,
    ) -> list[Document]:
        """Full-text search documents."""
        ...


class DocumentLinkRepository(Protocol):
    """Port interface for document link persistence."""

    async def get_by_id(self, link_id: UUID) -> DocumentLink | None:
        """Get link by ID."""
        ...

    async def create(self, link: DocumentLink) -> DocumentLink:
        """Create a new link."""
        ...

    async def create_many(self, links: list[DocumentLink]) -> list[DocumentLink]:
        """Create multiple links."""
        ...

    async def delete(self, link_id: UUID) -> None:
        """Delete a link."""
        ...

    async def delete_by_source(self, source_document_id: UUID) -> int:
        """Delete all links from a source document. Returns count deleted."""
        ...

    async def get_outgoing_links(
        self,
        document_id: UUID,
    ) -> list[DocumentLink]:
        """Get all outgoing links from a document."""
        ...

    async def get_incoming_links(
        self,
        document_id: UUID,
    ) -> list[DocumentLink]:
        """Get all incoming links to a document (backlinks)."""
        ...

    async def get_unresolved_links(
        self,
        vault_id: UUID,
    ) -> list[DocumentLink]:
        """Get all unresolved links in a vault."""
        ...

    async def count_outgoing(self, document_id: UUID) -> int:
        """Count outgoing links from a document."""
        ...

    async def count_incoming(self, document_id: UUID) -> int:
        """Count incoming links to a document."""
        ...

    async def update_resolved(
        self,
        resolved_links: list[tuple[UUID, UUID]],
    ) -> int:
        """Bulk update links with resolved target document IDs.

        Args:
            resolved_links: List of (link_id, target_document_id) tuples

        Returns:
            Number of links updated
        """
        ...


class TagRepository(Protocol):
    """Port interface for tag persistence."""

    async def get_by_id(self, tag_id: UUID) -> Tag | None:
        """Get tag by ID."""
        ...

    async def get_by_name(self, vault_id: UUID, name: str) -> Tag | None:
        """Get tag by vault ID and name."""
        ...

    async def create(self, tag: Tag) -> Tag:
        """Create a new tag."""
        ...

    async def get_or_create(self, vault_id: UUID, name: str) -> Tag:
        """Get existing tag or create new one."""
        ...

    async def update(self, tag: Tag) -> Tag:
        """Update an existing tag."""
        ...

    async def delete(self, tag_id: UUID) -> None:
        """Delete a tag."""
        ...

    async def list_by_vault(self, vault_id: UUID) -> list[Tag]:
        """List all tags in a vault."""
        ...


class DocumentTagRepository(Protocol):
    """Port interface for document-tag associations."""

    async def add_tag(
        self,
        document_id: UUID,
        tag_id: UUID,
        source: str = "inline",
    ) -> None:
        """Add a tag to a document."""
        ...

    async def remove_tag(self, document_id: UUID, tag_id: UUID) -> None:
        """Remove a tag from a document."""
        ...

    async def remove_all_tags(self, document_id: UUID) -> None:
        """Remove all tags from a document."""
        ...

    async def get_document_tags(self, document_id: UUID) -> list[Tag]:
        """Get all tags for a document."""
        ...

    async def get_documents_by_tag(self, tag_id: UUID) -> list[Document]:
        """Get all documents with a tag."""
        ...


class EmbeddingChunkRepository(Protocol):
    """Port interface for embedding chunk persistence."""

    async def create(self, chunk: EmbeddingChunk) -> EmbeddingChunk:
        """Create a new embedding chunk."""
        ...

    async def create_many(
        self,
        chunks: list[EmbeddingChunk],
    ) -> list[EmbeddingChunk]:
        """Create multiple embedding chunks."""
        ...

    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete all chunks for a document. Returns count deleted."""
        ...

    async def get_by_document(self, document_id: UUID) -> list[EmbeddingChunk]:
        """Get all chunks for a document."""
        ...

    async def search_similar(
        self,
        vault_id: UUID,
        embedding: list[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> list[tuple[EmbeddingChunk, float]]:
        """Search for similar chunks. Returns (chunk, similarity_score) tuples."""
        ...
