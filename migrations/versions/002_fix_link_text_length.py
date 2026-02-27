"""Fix link_text and display_text column lengths.

Revision ID: 002_fix_link_text
Revises: 001_initial_schema
Create Date: 2026-02-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change link_text and display_text from VARCHAR(500) to TEXT."""
    op.alter_column(
        'document_links',
        'link_text',
        existing_type=sa.VARCHAR(length=500),
        type_=sa.Text(),
        existing_nullable=False
    )
    op.alter_column(
        'document_links',
        'display_text',
        existing_type=sa.VARCHAR(length=500),
        type_=sa.Text(),
        existing_nullable=True
    )


def downgrade() -> None:
    """Revert to VARCHAR(500)."""
    # Note: This may fail if there's data longer than 500 chars
    op.alter_column(
        'document_links',
        'link_text',
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=500),
        existing_nullable=False
    )
    op.alter_column(
        'document_links',
        'display_text',
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=500),
        existing_nullable=True
    )
