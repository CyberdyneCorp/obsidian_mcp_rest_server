"""Tag SQLAlchemy models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


class TagModel(Base):
    """Tag database model."""

    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("vault_id", "slug", name="uq_tag_vault_slug"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    vault_id: Mapped[UUID] = mapped_column(ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_tag_id: Mapped[UUID | None] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), nullable=True)
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    vault = relationship("VaultModel", back_populates="tags")
    parent = relationship("TagModel", remote_side=[id], back_populates="children")
    children = relationship("TagModel", back_populates="parent", cascade="all, delete-orphan")
    documents = relationship("DocumentTagModel", back_populates="tag", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name})>"


class DocumentTagModel(Base):
    """Document-Tag association model."""

    __tablename__ = "document_tags"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[UUID] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="inline")

    # Relationships
    document = relationship("DocumentModel", back_populates="tags")
    tag = relationship("TagModel", back_populates="documents")

    def __repr__(self) -> str:
        return f"<DocumentTag(document_id={self.document_id}, tag_id={self.tag_id})>"
