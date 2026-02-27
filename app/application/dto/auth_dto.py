"""Authentication DTOs."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.entities.user import User


@dataclass
class UserDTO:
    """User data transfer object."""

    id: UUID
    email: str
    display_name: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None

    @classmethod
    def from_entity(cls, user: User) -> "UserDTO":
        """Create DTO from entity."""
        return cls(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )


@dataclass
class UserCreateDTO:
    """DTO for creating a user."""

    email: str
    password: str
    display_name: str


@dataclass
class LoginDTO:
    """DTO for login request."""

    email: str
    password: str


@dataclass
class TokenDTO:
    """DTO for JWT tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
