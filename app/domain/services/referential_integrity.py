"""Referential integrity service for foreign key handling."""

from uuid import UUID

from app.domain.ports.repositories import (
    RelationshipRepositoryPort,
    RowRepositoryPort,
    TableRepositoryPort,
)
from app.domain.entities.table_relationship import OnDeleteAction
from app.domain.exceptions import ReferentialIntegrityError


class ReferentialIntegrityService:
    """Service for managing referential integrity between tables.

    Handles:
    - FK validation when creating/updating rows
    - CASCADE delete when rows are removed
    - SET NULL handling
    - RESTRICT enforcement
    """

    def __init__(
        self,
        relationship_repo: RelationshipRepositoryPort,
        table_repo: TableRepositoryPort,
        row_repo: RowRepositoryPort,
    ) -> None:
        self.relationship_repo = relationship_repo
        self.table_repo = table_repo
        self.row_repo = row_repo

    async def validate_references(
        self,
        table_id: UUID,
        row_data: dict,
    ) -> None:
        """Validate that all reference columns point to existing rows.

        Args:
            table_id: The table containing the row
            row_data: The row data to validate

        Raises:
            ReferentialIntegrityError: If a reference is invalid
        """
        # Get relationships where this table is the source
        relationships = await self.relationship_repo.get_by_source_table(table_id)

        for relationship in relationships:
            column_name = relationship.source_column
            if column_name not in row_data:
                continue

            reference_value = row_data[column_name]
            if reference_value is None:
                continue

            # Check if the referenced row exists
            try:
                referenced_row_id = UUID(str(reference_value))
            except ValueError:
                raise ReferentialIntegrityError(
                    f"Invalid UUID in reference column '{column_name}': {reference_value}"
                )

            referenced_row = await self.row_repo.get_by_id(referenced_row_id)
            if not referenced_row:
                target_table = await self.table_repo.get_by_id(
                    relationship.target_table_id
                )
                target_name = target_table.name if target_table else "unknown"
                raise ReferentialIntegrityError(
                    f"Referenced row '{reference_value}' not found in table '{target_name}'",
                    target_table=target_name,
                )

            # Verify the row is in the correct target table
            if referenced_row.table_id != relationship.target_table_id:
                target_table = await self.table_repo.get_by_id(
                    relationship.target_table_id
                )
                target_name = target_table.name if target_table else "unknown"
                raise ReferentialIntegrityError(
                    f"Referenced row belongs to wrong table (expected '{target_name}')",
                    target_table=target_name,
                )

    async def handle_row_deletion(
        self,
        table_id: UUID,
        row_id: UUID,
    ) -> int:
        """Handle cascade operations when a row is deleted.

        Args:
            table_id: The table containing the deleted row
            row_id: The ID of the deleted row

        Returns:
            Number of cascaded deletions performed

        Raises:
            ReferentialIntegrityError: If RESTRICT prevents deletion
        """
        deleted_count = 0

        # Get relationships where this table is the target (rows reference this row)
        relationships = await self.relationship_repo.get_by_target_table(table_id)

        for relationship in relationships:
            source_table = await self.table_repo.get_by_id(
                relationship.source_table_id
            )
            if not source_table:
                continue

            # Find rows that reference the deleted row
            referencing_rows = await self.row_repo.get_referencing_rows(
                relationship.source_table_id,
                relationship.source_column,
                row_id,
            )

            if not referencing_rows:
                continue

            if relationship.on_delete == OnDeleteAction.RESTRICT:
                raise ReferentialIntegrityError(
                    f"Cannot delete row: {len(referencing_rows)} row(s) in "
                    f"'{source_table.name}' reference this row",
                    source_table=source_table.name,
                )

            elif relationship.on_delete == OnDeleteAction.CASCADE:
                # Delete all referencing rows (recursively)
                for ref_row in referencing_rows:
                    # Recursively handle cascade for the referencing row
                    deleted_count += await self.handle_row_deletion(
                        ref_row.table_id,
                        ref_row.id,
                    )
                    await self.row_repo.delete(ref_row.id)
                    await self.table_repo.increment_row_count(
                        ref_row.table_id, -1
                    )
                    deleted_count += 1

            elif relationship.on_delete == OnDeleteAction.SET_NULL:
                # Set the reference column to null
                for ref_row in referencing_rows:
                    ref_row.set_field(relationship.source_column, None)
                    await self.row_repo.update(ref_row)

        return deleted_count

    async def check_can_delete_table(self, table_id: UUID) -> None:
        """Check if a table can be deleted.

        Args:
            table_id: The table to check

        Raises:
            ReferentialIntegrityError: If RESTRICT relationships prevent deletion
        """
        # Check for RESTRICT relationships where this table is the target
        restrict_relationships = await self.relationship_repo.get_restrict_relationships(
            table_id
        )

        for relationship in restrict_relationships:
            source_table = await self.table_repo.get_by_id(
                relationship.source_table_id
            )
            if not source_table:
                continue

            # Check if any rows reference this table
            target_table = await self.table_repo.get_by_id(table_id)
            if target_table and target_table.row_count > 0:
                raise ReferentialIntegrityError(
                    f"Cannot delete table: relationship '{relationship.relationship_name}' "
                    f"from '{source_table.name}' has RESTRICT constraint",
                    source_table=source_table.name,
                )
