"""TableRelationship entity representing a foreign key relationship between tables."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


def _utcnow_naive() -> datetime:
    """Return UTC timestamp as naive datetime for TIMESTAMP WITHOUT TIME ZONE."""
    return datetime.now(UTC).replace(tzinfo=None)


class OnDeleteAction(StrEnum):
    """Action to take when a referenced row is deleted."""

    CASCADE = "CASCADE"  # Delete referencing rows
    SET_NULL = "SET_NULL"  # Set reference to null
    RESTRICT = "RESTRICT"  # Prevent deletion


@dataclass
class TableRelationship:
    """Entity representing a foreign key relationship between tables.

    Relationships define how rows in one table reference rows in another,
    and what happens when referenced rows are deleted.
    """

    id: UUID = field(default_factory=uuid4)
    vault_id: UUID = field(default_factory=uuid4)
    source_table_id: UUID = field(default_factory=uuid4)
    source_column: str = ""
    target_table_id: UUID = field(default_factory=uuid4)
    target_column: str = "id"
    relationship_name: str = ""
    on_delete: OnDeleteAction = OnDeleteAction.CASCADE
    created_at: datetime = field(default_factory=_utcnow_naive)

    @classmethod
    def create(
        cls,
        vault_id: UUID,
        source_table_id: UUID,
        source_column: str,
        target_table_id: UUID,
        relationship_name: str,
        target_column: str = "id",
        on_delete: OnDeleteAction | str = OnDeleteAction.CASCADE,
    ) -> "TableRelationship":
        """Factory method to create a new relationship.

        Args:
            vault_id: The vault this relationship belongs to
            source_table_id: Table containing the foreign key column
            source_column: Column name in source table (the FK)
            target_table_id: Table being referenced
            relationship_name: Human-readable name for the relationship
            target_column: Column in target table (default: 'id')
            on_delete: Action when target row is deleted
        """
        if isinstance(on_delete, str):
            on_delete = OnDeleteAction(on_delete)

        return cls(
            vault_id=vault_id,
            source_table_id=source_table_id,
            source_column=source_column,
            target_table_id=target_table_id,
            target_column=target_column,
            relationship_name=relationship_name,
            on_delete=on_delete,
        )

    def update_on_delete(self, action: OnDeleteAction | str) -> None:
        """Update the on_delete action."""
        if isinstance(action, str):
            action = OnDeleteAction(action)
        self.on_delete = action

    def update_name(self, name: str) -> None:
        """Update the relationship name."""
        self.relationship_name = name

    @property
    def is_cascade(self) -> bool:
        """Check if relationship uses CASCADE delete."""
        return self.on_delete == OnDeleteAction.CASCADE

    @property
    def is_set_null(self) -> bool:
        """Check if relationship uses SET NULL on delete."""
        return self.on_delete == OnDeleteAction.SET_NULL

    @property
    def is_restrict(self) -> bool:
        """Check if relationship uses RESTRICT (prevents deletion)."""
        return self.on_delete == OnDeleteAction.RESTRICT
