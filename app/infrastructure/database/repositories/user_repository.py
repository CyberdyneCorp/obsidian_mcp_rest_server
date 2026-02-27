"""PostgreSQL user repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.infrastructure.database.models.user import UserModel


class PostgresUserRepository:
    """PostgreSQL implementation of UserRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, user: User) -> User:
        """Create a new user."""
        model = self._to_model(user)
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def update(self, user: User) -> User:
        """Update an existing user."""
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.email = user.email
            model.password_hash = user.password_hash
            model.display_name = user.display_name
            model.is_active = user.is_active
            model.last_login_at = user.last_login_at
            await self.session.flush()
            return self._to_entity(model)

        return user

    async def delete(self, user_id: UUID) -> None:
        """Delete a user."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()

    def _to_entity(self, model: UserModel) -> User:
        """Convert model to entity."""
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            display_name=model.display_name,
            is_active=model.is_active,
            created_at=model.created_at,
            last_login_at=model.last_login_at,
        )

    def _to_model(self, entity: User) -> UserModel:
        """Convert entity to model."""
        return UserModel(
            id=entity.id,
            email=entity.email,
            password_hash=entity.password_hash,
            display_name=entity.display_name,
            is_active=entity.is_active,
            created_at=entity.created_at,
            last_login_at=entity.last_login_at,
        )
