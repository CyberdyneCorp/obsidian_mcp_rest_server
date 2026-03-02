"""TableRelationship SQLAlchemy model."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


def _utcnow_naive() -> datetime:
    """Return UTC timestamp as naive datetime for TIMESTAMP WITHOUT TIME ZONE."""
    return datetime.now(UTC).replace(tzinfo=None)


class TableRelationshipModel(Base):
    """TableRelationship database model."""

    __tablename__ = "table_relationships"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    vault_id: Mapped[UUID] = mapped_column(
        ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False
    )
    source_table_id: Mapped[UUID] = mapped_column(
        ForeignKey("data_tables.id", ondelete="CASCADE"), nullable=False
    )
    source_column: Mapped[str] = mapped_column(String(255), nullable=False)
    target_table_id: Mapped[UUID] = mapped_column(
        ForeignKey("data_tables.id", ondelete="CASCADE"), nullable=False
    )
    target_column: Mapped[str] = mapped_column(String(255), nullable=False, default="id")
    relationship_name: Mapped[str] = mapped_column(String(255), nullable=False)
    on_delete: Mapped[str] = mapped_column(String(20), nullable=False, default="CASCADE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow_naive)

    # Relationships
    vault = relationship("VaultModel", back_populates="table_relationships")
    source_table = relationship(
        "DataTableModel",
        foreign_keys=[source_table_id],
        back_populates="outgoing_relationships",
    )
    target_table = relationship(
        "DataTableModel",
        foreign_keys=[target_table_id],
        back_populates="incoming_relationships",
    )

    def __repr__(self) -> str:
        return f"<TableRelationship(id={self.id}, name={self.relationship_name})>"
