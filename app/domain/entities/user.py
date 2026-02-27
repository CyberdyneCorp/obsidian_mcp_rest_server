"""User entity."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class User:
    """User entity representing an authenticated user."""

    id: UUID = field(default_factory=uuid4)
    email: str = ""
    password_hash: str = ""
    display_name: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate user data."""
        if self.email and "@" not in self.email:
            raise ValueError("Invalid email format")

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False

    def activate(self) -> None:
        """Activate user account."""
        self.is_active = True
