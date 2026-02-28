"""Structured data tables

Revision ID: 003
Revises: 002
Create Date: 2025-02-27

Adds tables for structured data feature:
- data_tables: User-defined table definitions
- table_rows: Row data for tables
- table_relationships: Foreign key definitions between tables
- document_table_links: Links from documents to tables/rows
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # data_tables: Table definitions
    op.create_table(
        "data_tables",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "vault_id",
            UUID,
            sa.ForeignKey("vaults.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("schema", JSONB, nullable=False, default={}),
        sa.Column("row_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now()),
    )
    op.create_index("idx_data_tables_vault_id", "data_tables", ["vault_id"])
    op.create_index("idx_data_tables_vault_slug", "data_tables", ["vault_id", "slug"])
    op.create_unique_constraint(
        "uq_data_table_vault_slug", "data_tables", ["vault_id", "slug"]
    )

    # table_rows: Row data
    op.create_table(
        "table_rows",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "table_id",
            UUID,
            sa.ForeignKey("data_tables.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vault_id",
            UUID,
            sa.ForeignKey("vaults.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("data", JSONB, nullable=False, default={}),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now()),
    )
    op.create_index("idx_table_rows_table_id", "table_rows", ["table_id"])
    op.create_index("idx_table_rows_vault_id", "table_rows", ["vault_id"])
    # GIN index for JSONB data queries
    op.execute(
        "CREATE INDEX idx_table_rows_data ON table_rows USING gin(data)"
    )

    # table_relationships: FK definitions
    op.create_table(
        "table_relationships",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "vault_id",
            UUID,
            sa.ForeignKey("vaults.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_table_id",
            UUID,
            sa.ForeignKey("data_tables.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_column", sa.String(255), nullable=False),
        sa.Column(
            "target_table_id",
            UUID,
            sa.ForeignKey("data_tables.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_column", sa.String(255), nullable=False, default="id"),
        sa.Column("relationship_name", sa.String(255), nullable=False),
        sa.Column("on_delete", sa.String(20), nullable=False, default="CASCADE"),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
    )
    op.create_index(
        "idx_table_relationships_vault_id", "table_relationships", ["vault_id"]
    )
    op.create_index(
        "idx_table_relationships_source", "table_relationships", ["source_table_id"]
    )
    op.create_index(
        "idx_table_relationships_target", "table_relationships", ["target_table_id"]
    )

    # document_table_links: Track document references to tables/rows
    op.create_table(
        "document_table_links",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "vault_id",
            UUID,
            sa.ForeignKey("vaults.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            UUID,
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "table_id",
            UUID,
            sa.ForeignKey("data_tables.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "row_id",
            UUID,
            sa.ForeignKey("table_rows.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("link_type", sa.String(20), nullable=False),
        sa.Column("link_text", sa.String(500), nullable=False),
        sa.Column("position_start", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
    )
    op.create_index(
        "idx_doc_table_links_vault", "document_table_links", ["vault_id"]
    )
    op.create_index(
        "idx_doc_table_links_doc", "document_table_links", ["document_id"]
    )
    op.create_index(
        "idx_doc_table_links_table", "document_table_links", ["table_id"]
    )
    op.create_index(
        "idx_doc_table_links_row", "document_table_links", ["row_id"]
    )


def downgrade() -> None:
    # Drop tables in reverse order (respecting FK dependencies)
    op.drop_table("document_table_links")
    op.drop_table("table_relationships")
    op.drop_table("table_rows")
    op.drop_table("data_tables")
