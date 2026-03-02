"""PostgreSQL user repository implementation."""


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.repositories.base import BaseRepository


class PostgresUserRepository(BaseRepository[User, UserModel]):
    """PostgreSQL implementation of UserRepository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    def _get_model_class(self) -> type[UserModel]:
        return UserModel

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            self._logger.debug(f"Found user with email={email}")
            return self._to_entity(model)
        return None

    async def update(self, user: User) -> User:
        """Update an existing user."""
        model = await self._get_model_by_id(user.id)

        if model:
            model.email = user.email
            model.password_hash = user.password_hash
            model.display_name = user.display_name
            model.is_active = user.is_active
            model.last_login_at = user.last_login_at
            await self.session.flush()
            self._logger.info(f"Updated user id={user.id}")
            return self._to_entity(model)

        self._logger.warning(f"Cannot update user: not found with id={user.id}")
        return user

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
