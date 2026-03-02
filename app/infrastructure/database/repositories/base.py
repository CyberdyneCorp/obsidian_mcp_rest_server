"""Base repository with common CRUD operations."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

logger = logging.getLogger(__name__)

# Type variables for entity and model
EntityT = TypeVar("EntityT")
ModelT = TypeVar("ModelT")


class BaseRepository(ABC, Generic[EntityT, ModelT]):
    """Base repository with common CRUD patterns.

    Subclasses must implement:
    - _get_model_class(): Return the SQLAlchemy model class
    - _to_entity(model): Convert model to domain entity
    - _to_model(entity): Convert domain entity to model
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._logger = logging.getLogger(self.__class__.__module__)

    @abstractmethod
    def _get_model_class(self) -> type[ModelT]:
        """Return the SQLAlchemy model class."""
        ...

    @abstractmethod
    def _to_entity(self, model: ModelT) -> EntityT:
        """Convert database model to domain entity."""
        ...

    @abstractmethod
    def _to_model(self, entity: EntityT) -> ModelT:
        """Convert domain entity to database model."""
        ...

    async def get_by_id(self, entity_id: UUID) -> EntityT | None:
        """Get entity by ID."""
        model_class = self._get_model_class()
        stmt = select(model_class).where(model_class.id == entity_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            self._logger.debug(f"Found {model_class.__name__} with id={entity_id}")
            return self._to_entity(model)

        self._logger.debug(f"{model_class.__name__} not found with id={entity_id}")
        return None

    async def exists(self, entity_id: UUID) -> bool:
        """Check if an entity exists by ID."""
        model_class = self._get_model_class()
        stmt = (
            select(func.count())
            .select_from(model_class)
            .where(model_class.id == entity_id)  # type: ignore[attr-defined]
        )
        result = await self.session.execute(stmt)
        return (result.scalar() or 0) > 0

    async def create(self, entity: EntityT) -> EntityT:
        """Create a new entity."""
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.flush()

        model_class = self._get_model_class()
        self._logger.info(f"Created {model_class.__name__} with id={getattr(model, 'id', 'unknown')}")
        return self._to_entity(model)

    async def create_many(self, entities: list[EntityT]) -> list[EntityT]:
        """Create multiple entities in bulk."""
        if not entities:
            return []

        models = [self._to_model(e) for e in entities]
        self.session.add_all(models)
        await self.session.flush()

        model_class = self._get_model_class()
        self._logger.info(f"Created {len(models)} {model_class.__name__} entities")
        return [self._to_entity(m) for m in models]

    async def delete(self, entity_id: UUID) -> bool:
        """Delete an entity by ID. Returns True if deleted, False if not found."""
        model_class = self._get_model_class()
        stmt = select(model_class).where(model_class.id == entity_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()
            self._logger.info(f"Deleted {model_class.__name__} with id={entity_id}")
            return True

        self._logger.warning(f"Cannot delete {model_class.__name__}: not found with id={entity_id}")
        return False

    async def _get_model_by_id(self, entity_id: UUID) -> ModelT | None:
        """Get the raw model by ID (for updates)."""
        model_class = self._get_model_class()
        stmt = select(model_class).where(model_class.id == entity_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _list_by_filter(
        self,
        *conditions: ColumnElement[bool],
        order_by: Any | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[EntityT]:
        """List entities by filter conditions with optional ordering and pagination.

        Args:
            *conditions: SQLAlchemy filter conditions
            order_by: Column or list of columns to order by
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of entities matching the conditions
        """
        model_class = self._get_model_class()
        stmt = select(model_class)

        if conditions:
            stmt = stmt.where(*conditions)

        if order_by is not None:
            if isinstance(order_by, (list, tuple)):
                stmt = stmt.order_by(*order_by)
            else:
                stmt = stmt.order_by(order_by)

        if limit is not None:
            stmt = stmt.limit(limit)

        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        self._logger.debug(f"Listed {len(models)} {model_class.__name__} entities")
        return [self._to_entity(m) for m in models]

    async def _count_by_filter(self, *conditions: ColumnElement[bool]) -> int:
        """Count entities matching filter conditions.

        Args:
            *conditions: SQLAlchemy filter conditions

        Returns:
            Count of matching entities
        """
        model_class = self._get_model_class()
        stmt = select(func.count()).select_from(model_class)

        if conditions:
            stmt = stmt.where(*conditions)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _delete_by_filter(self, *conditions: ColumnElement[bool]) -> int:
        """Delete entities matching filter conditions.

        Args:
            *conditions: SQLAlchemy filter conditions

        Returns:
            Count of deleted entities
        """
        model_class = self._get_model_class()
        stmt = select(model_class)

        if conditions:
            stmt = stmt.where(*conditions)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        count = len(models)

        for model in models:
            await self.session.delete(model)

        await self.session.flush()
        self._logger.info(f"Deleted {count} {model_class.__name__} entities")
        return count

    async def _get_one_by_filter(
        self,
        *conditions: ColumnElement[bool],
    ) -> EntityT | None:
        """Get a single entity by filter conditions.

        Args:
            *conditions: SQLAlchemy filter conditions

        Returns:
            Entity or None if not found
        """
        model_class = self._get_model_class()
        stmt = select(model_class)

        if conditions:
            stmt = stmt.where(*conditions)

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._to_entity(model)
        return None
