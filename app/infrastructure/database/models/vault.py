"""Vault SQLAlchemy model."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


class VaultModel(Base):
    """Vault database model."""

    __tablename__ = "vaults"
    __table_args__ = (UniqueConstraint("user_id", "slug", name="uq_vault_user_slug"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("UserModel", back_populates="vaults")
    folders = relationship("FolderModel", back_populates="vault", cascade="all, delete-orphan")
    documents = relationship("DocumentModel", back_populates="vault", cascade="all, delete-orphan")
    tags = relationship("TagModel", back_populates="vault", cascade="all, delete-orphan")
    links = relationship("DocumentLinkModel", back_populates="vault", cascade="all, delete-orphan")

    # Structured data relationships
    data_tables = relationship(
        "DataTableModel", back_populates="vault", cascade="all, delete-orphan"
    )
    table_rows = relationship(
        "TableRowModel", back_populates="vault", cascade="all, delete-orphan"
    )
    table_relationships = relationship(
        "TableRelationshipModel", back_populates="vault", cascade="all, delete-orphan"
    )
    document_table_links = relationship(
        "DocumentTableLinkModel", back_populates="vault", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Vault(id={self.id}, name={self.name})>"
