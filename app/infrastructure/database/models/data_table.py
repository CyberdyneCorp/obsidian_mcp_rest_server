"""DataTable SQLAlchemy model."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


def _utcnow_naive() -> datetime:
    """Return UTC timestamp as naive datetime for TIMESTAMP WITHOUT TIME ZONE."""
    return datetime.now(UTC).replace(tzinfo=None)


class DataTableModel(Base):
    """DataTable database model."""

    __tablename__ = "data_tables"
    __table_args__ = (UniqueConstraint("vault_id", "slug", name="uq_data_table_vault_slug"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    vault_id: Mapped[UUID] = mapped_column(
        ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    schema: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow_naive)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow_naive, onupdate=_utcnow_naive
    )

    # Relationships
    vault = relationship("VaultModel", back_populates="data_tables")
    rows = relationship(
        "TableRowModel", back_populates="table", cascade="all, delete-orphan"
    )
    outgoing_relationships = relationship(
        "TableRelationshipModel",
        foreign_keys="TableRelationshipModel.source_table_id",
        back_populates="source_table",
        cascade="all, delete-orphan",
    )
    incoming_relationships = relationship(
        "TableRelationshipModel",
        foreign_keys="TableRelationshipModel.target_table_id",
        back_populates="target_table",
    )
    document_links = relationship(
        "DocumentTableLinkModel",
        back_populates="table",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DataTable(id={self.id}, name={self.name})>"
