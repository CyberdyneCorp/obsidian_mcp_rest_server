"""DocumentTableLink SQLAlchemy model."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


class DocumentTableLinkModel(Base):
    """DocumentTableLink database model.

    Tracks links from documents to tables or specific table rows.
    These are extracted from document content when parsing
    [[table:TableName]] or [[row:TableName/uuid]] syntax.
    """

    __tablename__ = "document_table_links"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    vault_id: Mapped[UUID] = mapped_column(
        ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    table_id: Mapped[UUID] = mapped_column(
        ForeignKey("data_tables.id", ondelete="CASCADE"), nullable=False
    )
    row_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("table_rows.id", ondelete="SET NULL"), nullable=True
    )
    link_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'table' or 'table_row'
    link_text: Mapped[str] = mapped_column(String(500), nullable=False)
    position_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    vault = relationship("VaultModel", back_populates="document_table_links")
    document = relationship("DocumentModel", back_populates="table_links")
    table = relationship("DataTableModel", back_populates="document_links")
    row = relationship("TableRowModel", back_populates="document_links")

    def __repr__(self) -> str:
        return f"<DocumentTableLink(id={self.id}, link_type={self.link_type})>"
