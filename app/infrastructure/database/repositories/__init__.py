"""Repository implementations."""

from app.infrastructure.database.repositories.user_repository import PostgresUserRepository
from app.infrastructure.database.repositories.vault_repository import PostgresVaultRepository
from app.infrastructure.database.repositories.folder_repository import PostgresFolderRepository
from app.infrastructure.database.repositories.document_repository import PostgresDocumentRepository
from app.infrastructure.database.repositories.link_repository import PostgresDocumentLinkRepository
from app.infrastructure.database.repositories.tag_repository import PostgresTagRepository
from app.infrastructure.database.repositories.embedding_repository import PostgresEmbeddingChunkRepository

__all__ = [
    "PostgresDocumentLinkRepository",
    "PostgresDocumentRepository",
    "PostgresEmbeddingChunkRepository",
    "PostgresFolderRepository",
    "PostgresTagRepository",
    "PostgresUserRepository",
    "PostgresVaultRepository",
]
