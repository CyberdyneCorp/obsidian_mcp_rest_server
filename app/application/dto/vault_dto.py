"""Vault DTOs."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.entities.vault import Vault


@dataclass
class VaultDTO:
    """Vault data transfer object."""

    id: UUID
    name: str
    slug: str
    description: str | None
    document_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, vault: Vault) -> "VaultDTO":
        """Create DTO from entity."""
        return cls(
            id=vault.id,
            name=vault.name,
            slug=vault.slug,
            description=vault.description,
            document_count=vault.document_count,
            created_at=vault.created_at,
            updated_at=vault.updated_at,
        )


@dataclass
class VaultCreateDTO:
    """DTO for creating a vault."""

    name: str
    description: str | None = None


@dataclass
class VaultUpdateDTO:
    """DTO for updating a vault."""

    name: str | None = None
    description: str | None = None
