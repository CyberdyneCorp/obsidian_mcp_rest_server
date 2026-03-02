"""TableRow SQLAlchemy model."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


def _utcnow_naive() -> datetime:
    """Return UTC timestamp as naive datetime for TIMESTAMP WITHOUT TIME ZONE."""
    return datetime.now(UTC).replace(tzinfo=None)


class TableRowModel(Base):
    """TableRow database model."""

    __tablename__ = "table_rows"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    table_id: Mapped[UUID] = mapped_column(
        ForeignKey("data_tables.id", ondelete="CASCADE"), nullable=False
    )
    vault_id: Mapped[UUID] = mapped_column(
        ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False
    )
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow_naive)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow_naive, onupdate=_utcnow_naive
    )

    # Relationships
    table = relationship("DataTableModel", back_populates="rows")
    vault = relationship("VaultModel", back_populates="table_rows")
    document_links = relationship(
        "DocumentTableLinkModel",
        back_populates="row",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<TableRow(id={self.id}, table_id={self.table_id})>"
