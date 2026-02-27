"""Folder SQLAlchemy model."""

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


class FolderModel(Base):
    """Folder database model."""

    __tablename__ = "folders"
    __table_args__ = (UniqueConstraint("vault_id", "path", name="uq_folder_vault_path"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    vault_id: Mapped[UUID] = mapped_column(ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("folders.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    vault = relationship("VaultModel", back_populates="folders")
    parent = relationship("FolderModel", remote_side=[id], back_populates="children")
    children = relationship("FolderModel", back_populates="parent", cascade="all, delete-orphan")
    documents = relationship("DocumentModel", back_populates="folder")

    def __repr__(self) -> str:
        return f"<Folder(id={self.id}, path={self.path})>"
