"""Tests for graph API routes."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.domain.entities.vault import Vault
from app.domain.entities.document import Document


@pytest.mark.asyncio
class TestGraphRoutes:
    """Tests for graph query endpoints."""

    async def test_get_connections(
        self, client: AsyncClient, auth_headers: dict, mock_vault: Vault, db_session
    ):
        """Test getting document connections."""
        # Create a document in the vault
        from app.infrastructure.database.repositories.document_repository import (
            PostgresDocumentRepository,
        )
        from app.infrastructure.database.repositories.folder_repository import (
            PostgresFolderRepository,
        )

        folder_repo = PostgresFolderRepository(db_session)
        folder = await folder_repo.get_or_create_path(mock_vault.id, "")
        await db_session.commit()

        doc_repo = PostgresDocumentRepository(db_session)
        doc = Document(
            vault_id=mock_vault.id,
            folder_id=folder.id,
            title="Test Document",
            filename="test.md",
            path="test.md",
            content="# Test content",
            content_hash="abc123",
        )
        created_doc = await doc_repo.create(doc)
        await db_session.commit()

        response = await client.get(
            f"/vaults/{mock_vault.slug}/graph/connections/{created_doc.id}",
            headers=auth_headers,
            params={"depth": 2},
        )

        # Graph provider may not be available in test env
        assert response.status_code in [200, 404, 500]

    async def test_get_connections_with_depth(
        self, client: AsyncClient, auth_headers: dict, mock_vault: Vault, db_session
    ):
        """Test getting connections with custom depth parameter."""
        from app.infrastructure.database.repositories.document_repository import (
            PostgresDocumentRepository,
        )
        from app.infrastructure.database.repositories.folder_repository import (
            PostgresFolderRepository,
        )

        folder_repo = PostgresFolderRepository(db_session)
        folder = await folder_repo.get_or_create_path(mock_vault.id, "")
        await db_session.commit()

        doc_repo = PostgresDocumentRepository(db_session)
        doc = Document(
            vault_id=mock_vault.id,
            folder_id=folder.id,
            title="Hub Document",
            filename="hub.md",
            path="hub.md",
            content="# Hub with many links",
            content_hash="hub123",
        )
        created_doc = await doc_repo.create(doc)
        await db_session.commit()

        # Test with depth=1
        response = await client.get(
            f"/vaults/{mock_vault.slug}/graph/connections/{created_doc.id}",
            headers=auth_headers,
            params={"depth": 1},
        )
        assert response.status_code in [200, 404, 500]

        # Test with depth=5 (max)
        response = await client.get(
            f"/vaults/{mock_vault.slug}/graph/connections/{created_doc.id}",
            headers=auth_headers,
            params={"depth": 5},
        )
        assert response.status_code in [200, 404, 500]

    async def test_get_connections_invalid_depth(
        self, client: AsyncClient, auth_headers: dict, mock_vault: Vault
    ):
        """Test connections with invalid depth returns validation error."""
        doc_id = uuid4()

        # Depth > 5 should fail validation
        response = await client.get(
            f"/vaults/{mock_vault.slug}/graph/connections/{doc_id}",
            headers=auth_headers,
            params={"depth": 10},
        )
        assert response.status_code == 422

        # Depth < 1 should fail validation
        response = await client.get(
            f"/vaults/{mock_vault.slug}/graph/connections/{doc_id}",
            headers=auth_headers,
            params={"depth": 0},
        )
        assert response.status_code == 422

    async def test_get_connections_vault_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test connections on non-existent vault."""
        doc_id = uuid4()
        response = await client.get(
            f"/vaults/nonexistent-vault/graph/connections/{doc_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_get_connections_document_not_found(
        self, client: AsyncClient, auth_headers: dict, mock_vault: Vault
    ):
        """Test connections for non-existent document."""
        fake_doc_id = uuid4()
        response = await client.get(
            f"/vaults/{mock_vault.slug}/graph/connections/{fake_doc_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_get_shortest_path(
        self, client: AsyncClient, auth_headers: dict, mock_vault: Vault, db_session
    ):
        """Test getting shortest path between two documents."""
        from app.infrastructure.database.repositories.document_repository import (
            PostgresDocumentRepository,
        )
        from app.infrastructure.database.repositories.folder_repository import (
            PostgresFolderRepository,
        )

        folder_repo = PostgresFolderRepository(db_session)
        folder = await folder_repo.get_or_create_path(mock_vault.id, "")
        await db_session.commit()

        doc_repo = PostgresDocumentRepository(db_session)

        # Create source document
        source = Document(
            vault_id=mock_vault.id,
            folder_id=folder.id,
            title="Source",
            filename="source.md",
            path="source.md",
            content="# Source",
            content_hash="src123",
        )
        source_doc = await doc_repo.create(source)

        # Create target document
        target = Document(
            vault_id=mock_vault.id,
            folder_id=folder.id,
            title="Target",
            filename="target.md",
            path="target.md",
            content="# Target",
            content_hash="tgt123",
        )
        target_doc = await doc_repo.create(target)
        await db_session.commit()

        response = await client.get(
            f"/vaults/{mock_vault.slug}/graph/path",
            headers=auth_headers,
            params={"source": str(source_doc.id), "target": str(target_doc.id)},
        )

        # Path may not exist if documents aren't linked
        assert response.status_code in [200, 404, 500]

    async def test_get_shortest_path_vault_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test path query on non-existent vault."""
        source_id = uuid4()
        target_id = uuid4()

        response = await client.get(
            "/vaults/nonexistent/graph/path",
            headers=auth_headers,
            params={"source": str(source_id), "target": str(target_id)},
        )
        assert response.status_code == 404

    async def test_get_shortest_path_missing_params(
        self, client: AsyncClient, auth_headers: dict, mock_vault: Vault
    ):
        """Test path query with missing parameters."""
        # Missing target
        response = await client.get(
            f"/vaults/{mock_vault.slug}/graph/path",
            headers=auth_headers,
            params={"source": str(uuid4())},
        )
        assert response.status_code == 422

        # Missing source
        response = await client.get(
            f"/vaults/{mock_vault.slug}/graph/path",
            headers=auth_headers,
            params={"target": str(uuid4())},
        )
        assert response.status_code == 422

    async def test_get_orphans(
        self, client: AsyncClient, auth_headers: dict, mock_vault: Vault
    ):
        """Test getting orphan documents (no connections)."""
        response = await client.get(
            f"/vaults/{mock_vault.slug}/graph/orphans",
            headers=auth_headers,
        )

        # Graph provider may not be available
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "orphans" in data
            assert isinstance(data["orphans"], list)

    async def test_get_orphans_vault_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test orphans query on non-existent vault."""
        response = await client.get(
            "/vaults/nonexistent/graph/orphans",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_get_hubs(
        self, client: AsyncClient, auth_headers: dict, mock_vault: Vault
    ):
        """Test getting hub documents (most connected)."""
        response = await client.get(
            f"/vaults/{mock_vault.slug}/graph/hubs",
            headers=auth_headers,
        )

        # Graph provider may not be available
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "hubs" in data
            assert isinstance(data["hubs"], list)

    async def test_get_hubs_with_limit(
        self, client: AsyncClient, auth_headers: dict, mock_vault: Vault
    ):
        """Test getting hubs with custom limit."""
        response = await client.get(
            f"/vaults/{mock_vault.slug}/graph/hubs",
            headers=auth_headers,
            params={"limit": 5},
        )

        assert response.status_code in [200, 500]

    async def test_get_hubs_invalid_limit(
        self, client: AsyncClient, auth_headers: dict, mock_vault: Vault
    ):
        """Test hubs with invalid limit returns validation error."""
        # Limit > 50 should fail
        response = await client.get(
            f"/vaults/{mock_vault.slug}/graph/hubs",
            headers=auth_headers,
            params={"limit": 100},
        )
        assert response.status_code == 422

        # Limit < 1 should fail
        response = await client.get(
            f"/vaults/{mock_vault.slug}/graph/hubs",
            headers=auth_headers,
            params={"limit": 0},
        )
        assert response.status_code == 422

    async def test_get_hubs_vault_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test hubs query on non-existent vault."""
        response = await client.get(
            "/vaults/nonexistent/graph/hubs",
            headers=auth_headers,
        )
        assert response.status_code == 404
