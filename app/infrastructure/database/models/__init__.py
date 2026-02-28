"""SQLAlchemy models."""

from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.models.vault import VaultModel
from app.infrastructure.database.models.folder import FolderModel
from app.infrastructure.database.models.document import DocumentModel
from app.infrastructure.database.models.document_link import DocumentLinkModel
from app.infrastructure.database.models.tag import TagModel, DocumentTagModel
from app.infrastructure.database.models.embedding_chunk import EmbeddingChunkModel
from app.infrastructure.database.models.data_table import DataTableModel
from app.infrastructure.database.models.table_row import TableRowModel
from app.infrastructure.database.models.table_relationship import TableRelationshipModel
from app.infrastructure.database.models.document_table_link import DocumentTableLinkModel

__all__ = [
    "DataTableModel",
    "DocumentLinkModel",
    "DocumentModel",
    "DocumentTableLinkModel",
    "DocumentTagModel",
    "EmbeddingChunkModel",
    "FolderModel",
    "TableRelationshipModel",
    "TableRowModel",
    "TagModel",
    "UserModel",
    "VaultModel",
]
