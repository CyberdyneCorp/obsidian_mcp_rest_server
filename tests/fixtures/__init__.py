"""Shared test fixtures and factory functions."""

from app.domain.entities.user import User
from app.domain.entities.vault import Vault
from app.domain.entities.folder import Folder
from app.domain.entities.document import Document


def create_test_user(
    email: str = "testuser@example.com",
    display_name: str = "Test User",
    is_active: bool = True,
) -> User:
    """Create a test user entity."""
    return User(
        email=email,
        password_hash="hashed_password_for_testing",
        display_name=display_name,
        is_active=is_active,
    )


def create_test_vault(
    user_id,
    name: str = "Test Vault",
    slug: str = "test-vault",
    document_count: int = 0,
) -> Vault:
    """Create a test vault entity."""
    return Vault(
        user_id=user_id,
        name=name,
        slug=slug,
        document_count=document_count,
    )


def create_test_folder(
    vault_id,
    name: str = "Notes",
    path: str = "Notes",
    depth: int = 0,
    parent_id=None,
) -> Folder:
    """Create a test folder entity."""
    return Folder(
        vault_id=vault_id,
        parent_id=parent_id,
        name=name,
        path=path,
        depth=depth,
    )


def create_test_document(
    vault_id,
    folder_id,
    title: str = "Test Document",
    filename: str = "Test Document.md",
    path: str = "Notes/Test Document.md",
    content: str = "# Test Document\n\nTest content.",
) -> Document:
    """Create a test document entity."""
    return Document(
        vault_id=vault_id,
        folder_id=folder_id,
        title=title,
        filename=filename,
        path=path,
        content=content,
        content_hash="test_hash",
    )
