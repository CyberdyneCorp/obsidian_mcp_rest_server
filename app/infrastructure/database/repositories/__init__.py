"""Repository implementations."""

from app.infrastructure.database.repositories.base import BaseRepository
from app.infrastructure.database.repositories.user_repository import PostgresUserRepository
from app.infrastructure.database.repositories.vault_repository import PostgresVaultRepository
from app.infrastructure.database.repositories.folder_repository import PostgresFolderRepository
from app.infrastructure.database.repositories.document_repository import PostgresDocumentRepository
from app.infrastructure.database.repositories.link_repository import PostgresDocumentLinkRepository
from app.infrastructure.database.repositories.tag_repository import PostgresTagRepository
from app.infrastructure.database.repositories.embedding_repository import PostgresEmbeddingChunkRepository
from app.infrastructure.database.repositories.table_repository import PostgresTableRepository
from app.infrastructure.database.repositories.row_repository import PostgresRowRepository
from app.infrastructure.database.repositories.relationship_repository import PostgresRelationshipRepository
from app.infrastructure.database.repositories.document_table_link_repository import PostgresDocumentTableLinkRepository

__all__ = [
    "BaseRepository",
    "PostgresDocumentLinkRepository",
    "PostgresDocumentRepository",
    "PostgresDocumentTableLinkRepository",
    "PostgresEmbeddingChunkRepository",
    "PostgresFolderRepository",
    "PostgresRelationshipRepository",
    "PostgresRowRepository",
    "PostgresTableRepository",
    "PostgresTagRepository",
    "PostgresUserRepository",
    "PostgresVaultRepository",
]
