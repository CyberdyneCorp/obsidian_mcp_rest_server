"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-02-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS age")

    # Users table
    op.create_table(
        "users",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_users_email", "users", ["email"])

    # Vaults table
    op.create_table(
        "vaults",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("document_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now()),
    )
    op.create_index("idx_vaults_user_id", "vaults", ["user_id"])
    op.create_index("idx_vaults_user_slug", "vaults", ["user_id", "slug"])
    op.create_unique_constraint("uq_vault_user_slug", "vaults", ["user_id", "slug"])

    # Folders table
    op.create_table(
        "folders",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("vault_id", UUID, sa.ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", UUID, sa.ForeignKey("folders.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column("depth", sa.Integer, default=0),
    )
    op.create_index("idx_folders_vault_id", "folders", ["vault_id"])
    op.create_index("idx_folders_parent_id", "folders", ["parent_id"])
    op.create_index("idx_folders_path", "folders", ["vault_id", "path"])
    op.create_unique_constraint("uq_folder_vault_path", "folders", ["vault_id", "path"])

    # Documents table
    op.create_table(
        "documents",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("vault_id", UUID, sa.ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False),
        sa.Column("folder_id", UUID, sa.ForeignKey("folders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column("content", sa.Text, nullable=False, default=""),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("frontmatter", JSONB, nullable=False, default={}),
        sa.Column("aliases", ARRAY(sa.Text), nullable=False, default=[]),
        sa.Column("word_count", sa.Integer, default=0),
        sa.Column("link_count", sa.Integer, default=0),
        sa.Column("backlink_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now()),
    )
    op.create_index("idx_documents_vault_id", "documents", ["vault_id"])
    op.create_index("idx_documents_folder_id", "documents", ["folder_id"])
    op.create_index("idx_documents_path", "documents", ["vault_id", "path"])
    op.create_index("idx_documents_title", "documents", ["vault_id", "title"])
    op.create_unique_constraint("uq_document_vault_path", "documents", ["vault_id", "path"])

    # Full-text search index
    op.execute(
        "CREATE INDEX idx_documents_fts ON documents USING gin(to_tsvector('english', content))"
    )

    # Document links table
    op.create_table(
        "document_links",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("vault_id", UUID, sa.ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_document_id", UUID, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_document_id", UUID, sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("link_text", sa.String(500), nullable=False),
        sa.Column("display_text", sa.String(500), nullable=True),
        sa.Column("link_type", sa.String(20), nullable=False, default="wikilink"),
        sa.Column("is_resolved", sa.Boolean, default=False),
        sa.Column("position_start", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
    )
    op.create_index("idx_links_vault_id", "document_links", ["vault_id"])
    op.create_index("idx_links_source", "document_links", ["source_document_id"])
    op.create_index("idx_links_target", "document_links", ["target_document_id"])

    # Tags table
    op.create_table(
        "tags",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("vault_id", UUID, sa.ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("parent_tag_id", UUID, sa.ForeignKey("tags.id", ondelete="CASCADE"), nullable=True),
        sa.Column("document_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
    )
    op.create_index("idx_tags_vault_id", "tags", ["vault_id"])
    op.create_index("idx_tags_parent", "tags", ["parent_tag_id"])
    op.create_unique_constraint("uq_tag_vault_slug", "tags", ["vault_id", "slug"])

    # Document tags table (M2M)
    op.create_table(
        "document_tags",
        sa.Column("document_id", UUID, sa.ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", UUID, sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("source", sa.String(20), nullable=False, default="inline"),
    )
    op.create_index("idx_document_tags_document", "document_tags", ["document_id"])
    op.create_index("idx_document_tags_tag", "document_tags", ["tag_id"])

    # Embedding chunks table
    op.create_table(
        "embedding_chunks",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("vault_id", UUID, sa.ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", UUID, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("token_count", sa.Integer, nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
    )
    op.create_index("idx_chunks_vault_id", "embedding_chunks", ["vault_id"])
    op.create_index("idx_chunks_document_id", "embedding_chunks", ["document_id"])
    op.create_unique_constraint("uq_chunk_document_index", "embedding_chunks", ["document_id", "chunk_index"])

    # HNSW index for vector similarity search
    op.execute(
        """
        CREATE INDEX idx_chunks_embedding ON embedding_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    # Create AGE graph
    op.execute("LOAD 'age'")
    op.execute("SET search_path = ag_catalog, '$user', public")
    op.execute("SELECT create_graph('obsidian_graph')")


def downgrade() -> None:
    # Drop AGE graph
    op.execute("LOAD 'age'")
    op.execute("SET search_path = ag_catalog, '$user', public")
    op.execute("SELECT drop_graph('obsidian_graph', true)")

    # Drop tables in reverse order
    op.drop_table("embedding_chunks")
    op.drop_table("document_tags")
    op.drop_table("tags")
    op.drop_table("document_links")
    op.drop_table("documents")
    op.drop_table("folders")
    op.drop_table("vaults")
    op.drop_table("users")
