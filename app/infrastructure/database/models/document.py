"""Document SQLAlchemy model."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


class DocumentModel(Base):
    """Document database model."""

    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("vault_id", "path", name="uq_document_vault_path"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    vault_id: Mapped[UUID] = mapped_column(ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False)
    folder_id: Mapped[UUID | None] = mapped_column(ForeignKey("folders.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    frontmatter: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    aliases: Mapped[list] = mapped_column(ARRAY(Text), nullable=False, default=list)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    link_count: Mapped[int] = mapped_column(Integer, default=0)
    backlink_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vault = relationship("VaultModel", back_populates="documents")
    folder = relationship("FolderModel", back_populates="documents")
    outgoing_links = relationship(
        "DocumentLinkModel",
        foreign_keys="DocumentLinkModel.source_document_id",
        back_populates="source_document",
        cascade="all, delete-orphan",
    )
    incoming_links = relationship(
        "DocumentLinkModel",
        foreign_keys="DocumentLinkModel.target_document_id",
        back_populates="target_document",
    )
    tags = relationship("DocumentTagModel", back_populates="document", cascade="all, delete-orphan")
    embedding_chunks = relationship("EmbeddingChunkModel", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title})>"
