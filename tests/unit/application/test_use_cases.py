"""Tests for application use cases."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.application.dto.document_dto import DocumentDTO, DocumentCreateDTO, DocumentUpdateDTO
from app.application.dto.vault_dto import VaultDTO, VaultCreateDTO
from app.application.dto.search_dto import SearchQueryDTO, SearchResultDTO
from app.application.use_cases.vault import (
    CreateVaultUseCase,
    GetVaultUseCase,
    ListVaultsUseCase,
)
from app.application.use_cases.document import (
    CreateDocumentUseCase,
    GetDocumentUseCase,
    ListDocumentsUseCase,
    UpdateDocumentUseCase,
)
from app.application.use_cases.search import SemanticSearchUseCase, FulltextSearchUseCase
from app.application.use_cases.link import GetBacklinksUseCase
from app.domain.entities.vault import Vault
from app.domain.entities.document import Document
from app.domain.entities.folder import Folder
from app.domain.entities.document_link import DocumentLink, LinkType
from app.domain.entities.embedding_chunk import EmbeddingChunk
from app.domain.exceptions import (
    VaultNotFoundError,
    DocumentNotFoundError,
    DuplicateVaultError,
)


class TestCreateVaultUseCase:
    """Tests for CreateVaultUseCase."""

    @pytest.mark.asyncio
    async def test_create_vault_success(self):
        """Test successful vault creation."""
        user_id = uuid4()
        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = None
        vault_repo.create.return_value = Vault(
            id=uuid4(),
            user_id=user_id,
            name="My Vault",
            slug="my-vault",
            document_count=0,
        )

        use_case = CreateVaultUseCase(vault_repo)
        result = await use_case.execute(
            user_id,
            VaultCreateDTO(name="My Vault"),
        )

        assert result.name == "My Vault"
        assert result.slug == "my-vault"
        vault_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_vault_duplicate_slug(self):
        """Test vault creation with duplicate slug."""
        user_id = uuid4()
        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=uuid4(),
            user_id=user_id,
            name="Existing",
            slug="my-vault",
        )

        use_case = CreateVaultUseCase(vault_repo)

        with pytest.raises(DuplicateVaultError):
            await use_case.execute(
                user_id,
                VaultCreateDTO(name="My Vault"),
            )


class TestGetVaultUseCase:
    """Tests for GetVaultUseCase."""

    @pytest.mark.asyncio
    async def test_get_vault_success(self):
        """Test getting existing vault."""
        user_id = uuid4()
        vault_id = uuid4()
        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=vault_id,
            user_id=user_id,
            name="My Vault",
            slug="my-vault",
            document_count=5,
        )

        use_case = GetVaultUseCase(vault_repo)
        result = await use_case.execute(user_id, "my-vault")

        assert result.id == vault_id
        assert result.name == "My Vault"
        vault_repo.get_by_slug.assert_called_once_with(user_id, "my-vault")

    @pytest.mark.asyncio
    async def test_get_vault_not_found(self):
        """Test getting non-existent vault."""
        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = None

        use_case = GetVaultUseCase(vault_repo)

        with pytest.raises(VaultNotFoundError):
            await use_case.execute(uuid4(), "nonexistent")


class TestListVaultsUseCase:
    """Tests for ListVaultsUseCase."""

    @pytest.mark.asyncio
    async def test_list_vaults_success(self):
        """Test listing user vaults."""
        user_id = uuid4()
        vault_repo = AsyncMock()
        vault_repo.list_by_user.return_value = [
            Vault(id=uuid4(), user_id=user_id, name="Vault 1", slug="vault-1"),
            Vault(id=uuid4(), user_id=user_id, name="Vault 2", slug="vault-2"),
        ]

        use_case = ListVaultsUseCase(vault_repo)
        result = await use_case.execute(user_id)

        assert len(result) == 2
        assert result[0].name == "Vault 1"
        assert result[1].name == "Vault 2"

    @pytest.mark.asyncio
    async def test_list_vaults_empty(self):
        """Test listing vaults for user with no vaults."""
        vault_repo = AsyncMock()
        vault_repo.list_by_user.return_value = []

        use_case = ListVaultsUseCase(vault_repo)
        result = await use_case.execute(uuid4())

        assert result == []


class TestCreateDocumentUseCase:
    """Tests for CreateDocumentUseCase."""

    @pytest.mark.asyncio
    async def test_create_document_success(self):
        """Test successful document creation."""
        user_id = uuid4()
        vault_id = uuid4()
        folder_id = uuid4()

        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=vault_id,
            user_id=user_id,
            name="Vault",
            slug="vault",
        )

        document_repo = AsyncMock()
        document_repo.get_by_path.return_value = None
        document_repo.create.return_value = Document(
            id=uuid4(),
            vault_id=vault_id,
            folder_id=folder_id,
            title="New Document",
            filename="New Document.md",
            path="Notes/New Document.md",
            content="# Content",
            content_hash="abc123",
        )

        folder_repo = AsyncMock()
        folder_repo.get_or_create_path.return_value = Folder(
            id=folder_id,
            vault_id=vault_id,
            name="Notes",
            path="Notes",
            depth=0,
        )

        use_case = CreateDocumentUseCase(vault_repo, document_repo, folder_repo)
        result = await use_case.execute(
            user_id,
            "vault",
            DocumentCreateDTO(
                path="Notes/New Document.md",
                content="# Content",
            ),
        )

        assert result.title == "New Document"
        assert result.path == "Notes/New Document.md"
        document_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_document_vault_not_found(self):
        """Test document creation with non-existent vault."""
        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = None

        use_case = CreateDocumentUseCase(vault_repo, AsyncMock(), AsyncMock())

        with pytest.raises(VaultNotFoundError):
            await use_case.execute(
                uuid4(),
                "nonexistent",
                DocumentCreateDTO(path="test.md", content="content"),
            )


class TestGetDocumentUseCase:
    """Tests for GetDocumentUseCase."""

    @pytest.mark.asyncio
    async def test_get_document_by_id(self):
        """Test getting document by ID."""
        user_id = uuid4()
        vault_id = uuid4()
        doc_id = uuid4()

        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=vault_id,
            user_id=user_id,
            name="Vault",
            slug="vault",
        )

        document_repo = AsyncMock()
        document_repo.get_by_id.return_value = Document(
            id=doc_id,
            vault_id=vault_id,
            folder_id=uuid4(),
            title="Test Doc",
            filename="test.md",
            path="test.md",
            content="# Test",
            content_hash="hash",
        )

        use_case = GetDocumentUseCase(vault_repo, document_repo)
        result = await use_case.execute(user_id, "vault", document_id=doc_id)

        assert result.id == doc_id
        assert result.title == "Test Doc"
        document_repo.get_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_by_path(self):
        """Test getting document by path."""
        user_id = uuid4()
        vault_id = uuid4()
        doc_id = uuid4()

        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=vault_id,
            user_id=user_id,
            name="Vault",
            slug="vault",
        )

        document_repo = AsyncMock()
        document_repo.get_by_path.return_value = Document(
            id=doc_id,
            vault_id=vault_id,
            folder_id=uuid4(),
            title="Test Doc",
            filename="test.md",
            path="Notes/test.md",
            content="# Test",
            content_hash="hash",
        )

        use_case = GetDocumentUseCase(vault_repo, document_repo)
        result = await use_case.execute(user_id, "vault", path="Notes/test.md")

        assert result.path == "Notes/test.md"
        document_repo.get_by_path.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_not_found(self):
        """Test getting non-existent document."""
        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=uuid4(),
            user_id=uuid4(),
            name="Vault",
            slug="vault",
        )

        document_repo = AsyncMock()
        document_repo.get_by_id.return_value = None

        use_case = GetDocumentUseCase(vault_repo, document_repo)

        with pytest.raises(DocumentNotFoundError):
            await use_case.execute(uuid4(), "vault", document_id=uuid4())


class TestListDocumentsUseCase:
    """Tests for ListDocumentsUseCase."""

    @pytest.mark.asyncio
    async def test_list_documents_success(self):
        """Test listing documents in vault."""
        user_id = uuid4()
        vault_id = uuid4()

        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=vault_id,
            user_id=user_id,
            name="Vault",
            slug="vault",
        )

        document_repo = AsyncMock()
        # list_by_vault returns just a list, count is separate
        document_repo.list_by_vault.return_value = [
            Document(
                id=uuid4(),
                vault_id=vault_id,
                folder_id=uuid4(),
                title=f"Doc {i}",
                filename=f"doc{i}.md",
                path=f"doc{i}.md",
                content="content",
                content_hash="hash",
            )
            for i in range(3)
        ]
        document_repo.count_by_vault.return_value = 3

        use_case = ListDocumentsUseCase(vault_repo, document_repo)
        docs, total = await use_case.execute(user_id, "vault", limit=10, offset=0)

        assert len(docs) == 3
        assert total == 3

    @pytest.mark.asyncio
    async def test_list_documents_with_folder_filter(self):
        """Test listing documents filtered by folder."""
        user_id = uuid4()
        vault_id = uuid4()

        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=vault_id,
            user_id=user_id,
            name="Vault",
            slug="vault",
        )

        document_repo = AsyncMock()
        # Create documents with folder path
        document_repo.list_by_vault.return_value = [
            Document(
                id=uuid4(),
                vault_id=vault_id,
                folder_id=uuid4(),
                title="Doc in Notes",
                filename="doc.md",
                path="Notes/doc.md",
                content="content",
                content_hash="hash",
            )
        ]
        document_repo.count_by_vault.return_value = 1

        use_case = ListDocumentsUseCase(vault_repo, document_repo)
        docs, total = await use_case.execute(user_id, "vault", folder="Notes")

        # Verify list_by_vault was called
        document_repo.list_by_vault.assert_called_once()
        assert len(docs) == 1


class TestUpdateDocumentUseCase:
    """Tests for UpdateDocumentUseCase."""

    @pytest.mark.asyncio
    async def test_update_document_content(self):
        """Test updating document content."""
        user_id = uuid4()
        vault_id = uuid4()
        doc_id = uuid4()

        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=vault_id,
            user_id=user_id,
            name="Vault",
            slug="vault",
        )

        existing_doc = Document(
            id=doc_id,
            vault_id=vault_id,
            folder_id=uuid4(),
            title="Test",
            filename="test.md",
            path="test.md",
            content="# Old",
            content_hash="old_hash",
        )

        document_repo = AsyncMock()
        document_repo.get_by_id.return_value = existing_doc
        document_repo.update.return_value = existing_doc

        link_repo = AsyncMock()

        use_case = UpdateDocumentUseCase(vault_repo, document_repo, link_repo)
        result = await use_case.execute(
            user_id,
            "vault",
            doc_id,
            DocumentUpdateDTO(content="# New Content"),
        )

        document_repo.update.assert_called_once()


class TestSemanticSearchUseCase:
    """Tests for SemanticSearchUseCase."""

    @pytest.mark.asyncio
    async def test_semantic_search_success(self):
        """Test successful semantic search."""
        user_id = uuid4()
        vault_id = uuid4()
        doc_id = uuid4()

        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=vault_id,
            user_id=user_id,
            name="Vault",
            slug="vault",
        )

        document_repo = AsyncMock()
        document_repo.get_by_id.return_value = Document(
            id=doc_id,
            vault_id=vault_id,
            folder_id=uuid4(),
            title="Relevant Doc",
            filename="doc.md",
            path="doc.md",
            content="content",
            content_hash="hash",
        )

        # search_similar returns list of (EmbeddingChunk, score) tuples
        chunk = EmbeddingChunk(
            vault_id=vault_id,
            document_id=doc_id,
            chunk_index=0,
            content="Matching chunk text",
            token_count=10,
        )
        embedding_repo = AsyncMock()
        embedding_repo.search_similar.return_value = [(chunk, 0.95)]

        embedding_provider = AsyncMock()
        embedding_provider.embed_text.return_value = [0.1] * 1536

        use_case = SemanticSearchUseCase(
            vault_repo=vault_repo,
            document_repo=document_repo,
            embedding_repo=embedding_repo,
            embedding_provider=embedding_provider,
        )

        results = await use_case.execute(
            user_id,
            "vault",
            SearchQueryDTO(query="search term", limit=10),
        )

        assert len(results) == 1
        assert results[0].score == 0.95
        embedding_provider.embed_text.assert_called_once_with("search term")


class TestFulltextSearchUseCase:
    """Tests for FulltextSearchUseCase."""

    @pytest.mark.asyncio
    async def test_fulltext_search_success(self):
        """Test successful full-text search."""
        user_id = uuid4()
        vault_id = uuid4()

        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=vault_id,
            user_id=user_id,
            name="Vault",
            slug="vault",
        )

        # search_fulltext returns a list of documents
        document_repo = AsyncMock()
        document_repo.search_fulltext.return_value = [
            Document(
                id=uuid4(),
                vault_id=vault_id,
                folder_id=uuid4(),
                title="Search Result",
                filename="result.md",
                path="result.md",
                content="content with keyword here for testing",
                content_hash="hash",
            ),
        ]

        use_case = FulltextSearchUseCase(vault_repo, document_repo)

        results = await use_case.execute(user_id, "vault", "keyword", limit=10)

        assert len(results) == 1
        # Headline is generated from content by the use case
        assert "keyword" in results[0].headline


class TestGetBacklinksUseCase:
    """Tests for GetBacklinksUseCase."""

    @pytest.mark.asyncio
    async def test_get_backlinks_success(self):
        """Test getting backlinks for a document."""
        user_id = uuid4()
        vault_id = uuid4()
        target_id = uuid4()
        source_id = uuid4()

        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=vault_id,
            user_id=user_id,
            name="Vault",
            slug="vault",
        )

        # Create source document for lookup
        source_doc = Document(
            id=source_id,
            vault_id=vault_id,
            folder_id=uuid4(),
            title="Source",
            filename="source.md",
            path="source.md",
            content="Links to [[Target]]",
            content_hash="hash",
        )

        # get_by_id returns target doc first, then source doc
        target_doc = Document(
            id=target_id,
            vault_id=vault_id,
            folder_id=uuid4(),
            title="Target",
            filename="target.md",
            path="target.md",
            content="content",
            content_hash="hash",
        )

        document_repo = AsyncMock()
        document_repo.get_by_id.side_effect = [target_doc, source_doc]

        # get_incoming_links returns DocumentLink entities
        link = DocumentLink(
            vault_id=vault_id,
            source_document_id=source_id,
            target_document_id=target_id,
            link_text="Target",
            link_type=LinkType.WIKILINK,
            is_resolved=True,
        )

        link_repo = AsyncMock()
        link_repo.get_incoming_links.return_value = [link]

        use_case = GetBacklinksUseCase(vault_repo, document_repo, link_repo)
        results = await use_case.execute(user_id, "vault", target_id)

        assert len(results) == 1
        assert results[0].document.title == "Source"
        assert results[0].link_text == "Target"


class TestExportVaultUseCase:
    """Tests for ExportVaultUseCase."""

    @pytest.mark.asyncio
    async def test_export_vault_success(self):
        """Test successful vault export."""
        import zipfile
        import io
        from app.application.use_cases.vault import ExportVaultUseCase
        from app.domain.value_objects.frontmatter import Frontmatter

        user_id = uuid4()
        vault_id = uuid4()

        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=vault_id,
            user_id=user_id,
            name="Test Vault",
            slug="test-vault",
            document_count=2,
        )

        # Create documents with frontmatter
        documents = [
            Document(
                id=uuid4(),
                vault_id=vault_id,
                folder_id=uuid4(),
                title="Welcome",
                filename="Welcome.md",
                path="Welcome.md",
                content="# Welcome\n\nWelcome to my vault.",
                content_hash="hash1",
                frontmatter=Frontmatter(tags=("welcome",)),
            ),
            Document(
                id=uuid4(),
                vault_id=vault_id,
                folder_id=uuid4(),
                title="Notes",
                filename="Notes.md",
                path="Notes/Notes.md",
                content="# Notes\n\nSome notes here.",
                content_hash="hash2",
                frontmatter=Frontmatter(title="My Notes", tags=("notes", "important")),
            ),
        ]

        document_repo = AsyncMock()
        document_repo.list_by_vault.return_value = documents

        folder_repo = AsyncMock()

        use_case = ExportVaultUseCase(vault_repo, document_repo, folder_repo)
        zip_bytes = await use_case.execute(user_id, "test-vault")

        # Verify ZIP content
        assert zip_bytes is not None
        assert len(zip_bytes) > 0

        # Open and verify ZIP structure
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            names = zf.namelist()
            assert "Welcome.md" in names
            assert "Notes/Notes.md" in names

            # Verify content includes frontmatter
            welcome_content = zf.read("Welcome.md").decode("utf-8")
            assert "# Welcome" in welcome_content

            notes_content = zf.read("Notes/Notes.md").decode("utf-8")
            assert "title: My Notes" in notes_content or "# Notes" in notes_content

    @pytest.mark.asyncio
    async def test_export_vault_not_found(self):
        """Test export of non-existent vault."""
        from app.application.use_cases.vault import ExportVaultUseCase

        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = None

        use_case = ExportVaultUseCase(vault_repo, AsyncMock(), AsyncMock())

        with pytest.raises(VaultNotFoundError):
            await use_case.execute(uuid4(), "nonexistent")

    @pytest.mark.asyncio
    async def test_export_empty_vault(self):
        """Test export of empty vault."""
        import zipfile
        import io
        from app.application.use_cases.vault import ExportVaultUseCase

        user_id = uuid4()
        vault_id = uuid4()

        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=vault_id,
            user_id=user_id,
            name="Empty Vault",
            slug="empty-vault",
            document_count=0,
        )

        document_repo = AsyncMock()
        document_repo.list_by_vault.return_value = []

        use_case = ExportVaultUseCase(vault_repo, document_repo, AsyncMock())
        zip_bytes = await use_case.execute(user_id, "empty-vault")

        # Should still return valid ZIP (just empty)
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            assert len(zf.namelist()) == 0

    @pytest.mark.asyncio
    async def test_export_preserves_folder_structure(self):
        """Test that export preserves nested folder structure."""
        import zipfile
        import io
        from app.application.use_cases.vault import ExportVaultUseCase

        user_id = uuid4()
        vault_id = uuid4()

        vault_repo = AsyncMock()
        vault_repo.get_by_slug.return_value = Vault(
            id=vault_id,
            user_id=user_id,
            name="Structured Vault",
            slug="structured-vault",
        )

        documents = [
            Document(
                id=uuid4(),
                vault_id=vault_id,
                title="Root Doc",
                filename="root.md",
                path="root.md",
                content="Root level",
                content_hash="h1",
            ),
            Document(
                id=uuid4(),
                vault_id=vault_id,
                title="Level 1",
                filename="doc.md",
                path="Projects/doc.md",
                content="Project doc",
                content_hash="h2",
            ),
            Document(
                id=uuid4(),
                vault_id=vault_id,
                title="Level 2",
                filename="deep.md",
                path="Projects/2024/Q1/deep.md",
                content="Deep nested",
                content_hash="h3",
            ),
        ]

        document_repo = AsyncMock()
        document_repo.list_by_vault.return_value = documents

        use_case = ExportVaultUseCase(vault_repo, document_repo, AsyncMock())
        zip_bytes = await use_case.execute(user_id, "structured-vault")

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            names = zf.namelist()
            assert "root.md" in names
            assert "Projects/doc.md" in names
            assert "Projects/2024/Q1/deep.md" in names
