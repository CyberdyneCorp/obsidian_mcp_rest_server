"""DocumentLink SQLAlchemy model."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


def _utcnow_naive() -> datetime:
    """Return UTC timestamp as naive datetime for TIMESTAMP WITHOUT TIME ZONE."""
    return datetime.now(UTC).replace(tzinfo=None)


class DocumentLinkModel(Base):
    """DocumentLink database model."""

    __tablename__ = "document_links"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    vault_id: Mapped[UUID] = mapped_column(ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False)
    source_document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    target_document_id: Mapped[UUID | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    link_text: Mapped[str] = mapped_column(Text, nullable=False)  # Changed from String(500) to Text
    display_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # Changed from String(500) to Text
    link_type: Mapped[str] = mapped_column(String(20), nullable=False, default="wikilink")
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    position_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow_naive)

    # Relationships
    vault = relationship("VaultModel", back_populates="links")
    source_document = relationship(
        "DocumentModel",
        foreign_keys=[source_document_id],
        back_populates="outgoing_links",
    )
    target_document = relationship(
        "DocumentModel",
        foreign_keys=[target_document_id],
        back_populates="incoming_links",
    )

    def __repr__(self) -> str:
        return f"<DocumentLink(id={self.id}, text={self.link_text})>"
