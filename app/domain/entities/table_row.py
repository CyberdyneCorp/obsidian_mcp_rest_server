"""TableRow entity representing a row of data in a table."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


def _utcnow_naive() -> datetime:
    """Return UTC timestamp as naive datetime for TIMESTAMP WITHOUT TIME ZONE."""
    return datetime.now(UTC).replace(tzinfo=None)


@dataclass
class TableRow:
    """Entity representing a row in a data table.

    Rows contain JSONB data that should conform to the parent table's schema.
    The data is stored as a dictionary where keys are column names.
    """

    id: UUID = field(default_factory=uuid4)
    table_id: UUID = field(default_factory=uuid4)
    vault_id: UUID = field(default_factory=uuid4)
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow_naive)
    updated_at: datetime = field(default_factory=_utcnow_naive)

    @classmethod
    def create(
        cls,
        table_id: UUID,
        vault_id: UUID,
        data: dict[str, Any] | None = None,
    ) -> "TableRow":
        """Factory method to create a new row.

        Args:
            table_id: The table this row belongs to
            vault_id: The vault this row belongs to
            data: Row data as a dictionary
        """
        return cls(
            table_id=table_id,
            vault_id=vault_id,
            data=data or {},
        )

    def update_data(self, data: dict[str, Any]) -> None:
        """Replace all row data."""
        self.data = data
        self._touch()

    def patch_data(self, updates: dict[str, Any]) -> None:
        """Partially update row data (merge)."""
        self.data.update(updates)
        self._touch()

    def set_field(self, field_name: str, value: Any) -> None:
        """Set a single field value."""
        self.data[field_name] = value
        self._touch()

    def get_field(self, field_name: str, default: Any = None) -> Any:
        """Get a field value."""
        return self.data.get(field_name, default)

    def remove_field(self, field_name: str) -> None:
        """Remove a field from the data."""
        if field_name in self.data:
            del self.data[field_name]
            self._touch()

    def has_field(self, field_name: str) -> bool:
        """Check if a field exists in the data."""
        return field_name in self.data

    def _touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = _utcnow_naive()

    @property
    def field_names(self) -> list[str]:
        """Get list of field names in this row's data."""
        return list(self.data.keys())

    def to_dict(self) -> dict[str, Any]:
        """Convert row to dictionary representation."""
        return {
            "id": str(self.id),
            "table_id": str(self.table_id),
            "vault_id": str(self.vault_id),
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
