"""PostgreSQL table relationship repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.table_relationship import TableRelationship, OnDeleteAction
from app.infrastructure.database.models.table_relationship import TableRelationshipModel
from app.infrastructure.database.repositories.base import BaseRepository


class PostgresRelationshipRepository(BaseRepository[TableRelationship, TableRelationshipModel]):
    """PostgreSQL implementation of RelationshipRepository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    def _get_model_class(self) -> type[TableRelationshipModel]:
        return TableRelationshipModel

    async def list_by_vault(self, vault_id: UUID) -> list[TableRelationship]:
        """List all relationships in a vault."""
        stmt = (
            select(TableRelationshipModel)
            .where(TableRelationshipModel.vault_id == vault_id)
            .order_by(TableRelationshipModel.created_at)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        self._logger.debug(f"Listed {len(models)} relationships in vault={vault_id}")
        return [self._to_entity(m) for m in models]

    async def get_by_source_table(
        self, source_table_id: UUID
    ) -> list[TableRelationship]:
        """Get all relationships where the given table is the source."""
        stmt = select(TableRelationshipModel).where(
            TableRelationshipModel.source_table_id == source_table_id
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        self._logger.debug(f"Found {len(models)} relationships from source table={source_table_id}")
        return [self._to_entity(m) for m in models]

    async def get_by_target_table(
        self, target_table_id: UUID
    ) -> list[TableRelationship]:
        """Get all relationships where the given table is the target."""
        stmt = select(TableRelationshipModel).where(
            TableRelationshipModel.target_table_id == target_table_id
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        self._logger.debug(f"Found {len(models)} relationships to target table={target_table_id}")
        return [self._to_entity(m) for m in models]

    async def get_by_source_column(
        self,
        source_table_id: UUID,
        source_column: str,
    ) -> TableRelationship | None:
        """Get relationship for a specific source table and column."""
        stmt = select(TableRelationshipModel).where(
            TableRelationshipModel.source_table_id == source_table_id,
            TableRelationshipModel.source_column == source_column,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            self._logger.debug(
                f"Found relationship for column={source_column} in table={source_table_id}"
            )
            return self._to_entity(model)
        return None

    async def get_cascade_relationships(
        self, target_table_id: UUID
    ) -> list[TableRelationship]:
        """Get relationships with CASCADE delete for a target table."""
        stmt = select(TableRelationshipModel).where(
            TableRelationshipModel.target_table_id == target_table_id,
            TableRelationshipModel.on_delete == OnDeleteAction.CASCADE.value,
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        self._logger.debug(
            f"Found {len(models)} CASCADE relationships for table={target_table_id}"
        )
        return [self._to_entity(m) for m in models]

    async def get_restrict_relationships(
        self, target_table_id: UUID
    ) -> list[TableRelationship]:
        """Get relationships with RESTRICT delete for a target table."""
        stmt = select(TableRelationshipModel).where(
            TableRelationshipModel.target_table_id == target_table_id,
            TableRelationshipModel.on_delete == OnDeleteAction.RESTRICT.value,
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        self._logger.debug(
            f"Found {len(models)} RESTRICT relationships for table={target_table_id}"
        )
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: TableRelationshipModel) -> TableRelationship:
        """Convert model to entity."""
        return TableRelationship(
            id=model.id,
            vault_id=model.vault_id,
            source_table_id=model.source_table_id,
            source_column=model.source_column,
            target_table_id=model.target_table_id,
            target_column=model.target_column,
            relationship_name=model.relationship_name,
            on_delete=OnDeleteAction(model.on_delete),
            created_at=model.created_at,
        )

    def _to_model(self, entity: TableRelationship) -> TableRelationshipModel:
        """Convert entity to model."""
        return TableRelationshipModel(
            id=entity.id,
            vault_id=entity.vault_id,
            source_table_id=entity.source_table_id,
            source_column=entity.source_column,
            target_table_id=entity.target_table_id,
            target_column=entity.target_column,
            relationship_name=entity.relationship_name,
            on_delete=entity.on_delete.value,
            created_at=entity.created_at,
        )
