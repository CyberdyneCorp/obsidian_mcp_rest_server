"""BDD test configuration and shared step definitions."""

import io
import zipfile
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pytest_bdd import given, when, then, parsers

from app.domain.entities.user import User
from app.domain.entities.vault import Vault
from app.domain.entities.document import Document
from app.domain.entities.folder import Folder
from app.domain.entities.tag import Tag
from app.domain.entities.document_link import DocumentLink


@pytest.fixture
def context() -> dict[str, Any]:
    """Shared context for BDD scenarios."""
    return {}


@pytest.fixture
def mock_repositories() -> dict[str, AsyncMock]:
    """Create mock repositories for testing."""
    return {
        "vault_repo": AsyncMock(),
        "document_repo": AsyncMock(),
        "folder_repo": AsyncMock(),
        "link_repo": AsyncMock(),
        "tag_repo": AsyncMock(),
        "embedding_repo": AsyncMock(),
        "user_repo": AsyncMock(),
        "table_repo": AsyncMock(),
        "row_repo": AsyncMock(),
        "relationship_repo": AsyncMock(),
        "document_table_link_repo": AsyncMock(),
    }


@pytest.fixture
def mock_providers() -> dict[str, AsyncMock]:
    """Create mock providers for testing."""
    return {
        "embedding_provider": AsyncMock(),
        "graph_provider": AsyncMock(),
    }


# Shared step definitions
@given("a registered user exists")
def given_registered_user(context: dict, mock_repositories: dict):
    """Create a registered user in context."""
    user = User(
        id=uuid4(),
        email="testuser@example.com",
        password_hash="hashed_password",
        display_name="Test User",
        is_active=True,
    )
    context["user"] = user
    mock_repositories["user_repo"].get_by_id.return_value = user


@given("the user is authenticated")
def given_authenticated_user(context: dict):
    """Mark user as authenticated."""
    context["authenticated"] = True
    context["auth_token"] = "mock_jwt_token"


@given(parsers.parse('a vault "{vault_slug}" exists with documents'))
def given_vault_with_documents(
    context: dict,
    mock_repositories: dict,
    vault_slug: str,
):
    """Create a vault with sample documents."""
    vault = Vault(
        id=uuid4(),
        user_id=context["user"].id,
        name=vault_slug.replace("-", " ").title(),
        slug=vault_slug,
        document_count=3,
    )
    context["vault"] = vault

    # Create sample documents
    folder = Folder(
        id=uuid4(),
        vault_id=vault.id,
        name="Notes",
        path="Notes",
        depth=0,
    )

    documents = [
        Document(
            id=uuid4(),
            vault_id=vault.id,
            folder_id=folder.id,
            title="Project Planning",
            filename="Project Planning.md",
            path="Notes/Project Planning.md",
            content="# Project Planning\n\nLinks to [[Reference]] and [[Tasks]].",
            content_hash="hash1",
            link_count=2,
        ),
        Document(
            id=uuid4(),
            vault_id=vault.id,
            folder_id=folder.id,
            title="Reference",
            filename="Reference.md",
            path="Notes/Reference.md",
            content="# Reference\n\nUseful information here.",
            content_hash="hash2",
            backlink_count=2,
        ),
        Document(
            id=uuid4(),
            vault_id=vault.id,
            folder_id=folder.id,
            title="Tasks",
            filename="Tasks.md",
            path="Notes/Tasks.md",
            content="# Tasks\n\nTodo items. See [[Reference]].",
            content_hash="hash3",
            link_count=1,
        ),
    ]

    context["documents"] = {d.title: d for d in documents}
    context["folder"] = folder

    # Configure mocks
    mock_repositories["vault_repo"].get_by_slug.return_value = vault
    mock_repositories["document_repo"].list_by_vault.return_value = (documents, len(documents))

    def get_doc_by_id(vault_id, doc_id):
        for doc in documents:
            if doc.id == doc_id:
                return doc
        return None

    mock_repositories["document_repo"].get_by_id.side_effect = get_doc_by_id


def create_test_zip(files: dict[str, str]) -> bytes:
    """Create a ZIP file from a dictionary of paths to content."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    buffer.seek(0)
    return buffer.read()
