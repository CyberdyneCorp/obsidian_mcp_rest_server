"""Integration tests for repository implementations."""

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.entities.vault import Vault
from app.domain.entities.document import Document
from app.domain.entities.folder import Folder
from app.domain.entities.tag import Tag
from app.domain.entities.document_link import DocumentLink
from app.infrastructure.database.repositories.user_repository import (
    PostgresUserRepository,
)
from app.infrastructure.database.repositories.vault_repository import (
    PostgresVaultRepository,
)
from app.infrastructure.database.repositories.document_repository import (
    PostgresDocumentRepository,
)
from app.infrastructure.database.repositories.folder_repository import (
    PostgresFolderRepository,
)
from app.infrastructure.database.repositories.tag_repository import (
    PostgresTagRepository,
)
from app.infrastructure.database.repositories.link_repository import (
    PostgresDocumentLinkRepository,
)


@pytest.mark.integration
class TestUserRepository:
    """Tests for PostgresUserRepository."""

    @pytest.mark.asyncio
    async def test_create_user(self, session: AsyncSession, clean_db):
        """Test creating a user."""
        repo = PostgresUserRepository(session)

        user = User(
            email="newuser@test.com",
            password_hash="hashed",
            display_name="New User",
        )

        created = await repo.create(user)
        await session.commit()

        assert created.id is not None
        assert created.email == "newuser@test.com"

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, session: AsyncSession, test_user: User):
        """Test getting user by email."""
        repo = PostgresUserRepository(session)

        found = await repo.get_by_email(test_user.email)

        assert found is not None
        assert found.id == test_user.id
        assert found.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, session: AsyncSession, test_user: User):
        """Test getting user by ID."""
        repo = PostgresUserRepository(session)

        found = await repo.get_by_id(test_user.id)

        assert found is not None
        assert found.id == test_user.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, session: AsyncSession, clean_db):
        """Test getting non-existent user returns None."""
        repo = PostgresUserRepository(session)

        found = await repo.get_by_email("nonexistent@test.com")

        assert found is None


@pytest.mark.integration
class TestVaultRepository:
    """Tests for PostgresVaultRepository."""

    @pytest.mark.asyncio
    async def test_create_vault(self, session: AsyncSession, test_user: User):
        """Test creating a vault."""
        repo = PostgresVaultRepository(session)

        vault = Vault(
            user_id=test_user.id,
            name="New Vault",
            slug="new-vault",
        )

        created = await repo.create(vault)
        await session.commit()

        assert created.id is not None
        assert created.name == "New Vault"
        assert created.slug == "new-vault"

    @pytest.mark.asyncio
    async def test_get_vault_by_slug(self, session: AsyncSession, test_vault: Vault):
        """Test getting vault by slug."""
        repo = PostgresVaultRepository(session)

        found = await repo.get_by_slug(test_vault.user_id, test_vault.slug)

        assert found is not None
        assert found.id == test_vault.id
        assert found.slug == test_vault.slug

    @pytest.mark.asyncio
    async def test_list_vaults_by_user(
        self, session: AsyncSession, test_user: User, test_vault: Vault
    ):
        """Test listing vaults by user."""
        repo = PostgresVaultRepository(session)

        vaults = await repo.list_by_user(test_user.id)

        assert len(vaults) >= 1
        assert any(v.id == test_vault.id for v in vaults)

    @pytest.mark.asyncio
    async def test_update_vault(self, session: AsyncSession, test_vault: Vault):
        """Test updating a vault."""
        repo = PostgresVaultRepository(session)

        test_vault.description = "Updated description"
        updated = await repo.update(test_vault)
        await session.commit()

        assert updated.description == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_vault(self, session: AsyncSession, test_user: User):
        """Test deleting a vault."""
        repo = PostgresVaultRepository(session)

        vault = Vault(
            user_id=test_user.id,
            name="To Delete",
            slug="to-delete",
        )
        created = await repo.create(vault)
        await session.commit()

        await repo.delete(created.id)
        await session.commit()

        found = await repo.get_by_slug(test_user.id, "to-delete")
        assert found is None


@pytest.mark.integration
class TestDocumentRepository:
    """Tests for PostgresDocumentRepository."""

    @pytest_asyncio.fixture
    async def test_folder(self, session: AsyncSession, test_vault: Vault) -> Folder:
        """Create test folder."""
        repo = PostgresFolderRepository(session)

        folder = Folder(
            vault_id=test_vault.id,
            name="Notes",
            path="Notes",
            depth=0,
        )

        created = await repo.create(folder)
        await session.commit()
        return created

    @pytest.mark.asyncio
    async def test_create_document(
        self, session: AsyncSession, test_vault: Vault, test_folder: Folder
    ):
        """Test creating a document."""
        repo = PostgresDocumentRepository(session)

        doc = Document(
            vault_id=test_vault.id,
            folder_id=test_folder.id,
            title="Test Document",
            filename="test.md",
            path="Notes/test.md",
            content="# Test\n\nContent here.",
            content_hash="abc123",
        )

        created = await repo.create(doc)
        await session.commit()

        assert created.id is not None
        assert created.title == "Test Document"

    @pytest.mark.asyncio
    async def test_get_document_by_path(
        self, session: AsyncSession, test_vault: Vault, test_folder: Folder
    ):
        """Test getting document by path."""
        repo = PostgresDocumentRepository(session)

        doc = Document(
            vault_id=test_vault.id,
            folder_id=test_folder.id,
            title="Path Test",
            filename="pathtest.md",
            path="Notes/pathtest.md",
            content="# Path Test",
            content_hash="def456",
        )

        await repo.create(doc)
        await session.commit()

        found = await repo.get_by_path(test_vault.id, "Notes/pathtest.md")

        assert found is not None
        assert found.path == "Notes/pathtest.md"

    @pytest.mark.asyncio
    async def test_list_documents_by_vault(
        self, session: AsyncSession, test_vault: Vault, test_folder: Folder
    ):
        """Test listing documents by vault."""
        repo = PostgresDocumentRepository(session)

        # Create multiple documents
        for i in range(3):
            doc = Document(
                vault_id=test_vault.id,
                folder_id=test_folder.id,
                title=f"Doc {i}",
                filename=f"doc{i}.md",
                path=f"Notes/doc{i}.md",
                content=f"# Doc {i}",
                content_hash=f"hash{i}",
            )
            await repo.create(doc)

        await session.commit()

        docs = await repo.list_by_vault(test_vault.id, limit=10, offset=0)

        assert len(docs) >= 3

    @pytest.mark.asyncio
    async def test_list_documents_with_folder_filter(
        self, session: AsyncSession, test_vault: Vault, test_folder: Folder
    ):
        """Test listing documents filtered by folder."""
        repo = PostgresDocumentRepository(session)

        # Create document in test folder
        doc = Document(
            vault_id=test_vault.id,
            folder_id=test_folder.id,
            title="In Notes",
            filename="innotes.md",
            path="Notes/innotes.md",
            content="# In Notes",
            content_hash="innotes",
        )
        await repo.create(doc)
        await session.commit()

        # Use list_by_folder for folder filtering
        docs = await repo.list_by_folder(test_folder.id)

        assert len(docs) >= 1
        for d in docs:
            assert d.folder_id == test_folder.id

    @pytest.mark.asyncio
    async def test_update_document(
        self, session: AsyncSession, test_vault: Vault, test_folder: Folder
    ):
        """Test updating a document."""
        repo = PostgresDocumentRepository(session)

        doc = Document(
            vault_id=test_vault.id,
            folder_id=test_folder.id,
            title="To Update",
            filename="update.md",
            path="Notes/update.md",
            content="# Original",
            content_hash="original",
        )

        created = await repo.create(doc)
        await session.commit()

        created.content = "# Updated Content"
        created.content_hash = "updated"
        updated = await repo.update(created)
        await session.commit()

        assert updated.content == "# Updated Content"

    @pytest.mark.asyncio
    async def test_delete_document(
        self, session: AsyncSession, test_vault: Vault, test_folder: Folder
    ):
        """Test deleting a document."""
        repo = PostgresDocumentRepository(session)

        doc = Document(
            vault_id=test_vault.id,
            folder_id=test_folder.id,
            title="To Delete",
            filename="delete.md",
            path="Notes/delete.md",
            content="# Delete Me",
            content_hash="delete",
        )

        created = await repo.create(doc)
        await session.commit()

        await repo.delete(created.id)
        await session.commit()

        found = await repo.get_by_id(created.id)
        assert found is None


@pytest.mark.integration
class TestFolderRepository:
    """Tests for PostgresFolderRepository."""

    @pytest.mark.asyncio
    async def test_create_folder(self, session: AsyncSession, test_vault: Vault):
        """Test creating a folder."""
        repo = PostgresFolderRepository(session)

        folder = Folder(
            vault_id=test_vault.id,
            name="Projects",
            path="Projects",
            depth=0,
        )

        created = await repo.create(folder)
        await session.commit()

        assert created.id is not None
        assert created.name == "Projects"

    @pytest.mark.asyncio
    async def test_get_or_create_path(self, session: AsyncSession, test_vault: Vault):
        """Test getting or creating folder path."""
        repo = PostgresFolderRepository(session)

        # First call creates the folder
        folder1 = await repo.get_or_create_path(test_vault.id, "NewFolder")
        await session.commit()

        assert folder1 is not None
        assert folder1.path == "NewFolder"

        # Second call returns existing folder
        folder2 = await repo.get_or_create_path(test_vault.id, "NewFolder")

        assert folder2.id == folder1.id

    @pytest.mark.asyncio
    async def test_create_nested_folders(
        self, session: AsyncSession, test_vault: Vault
    ):
        """Test creating nested folder structure."""
        repo = PostgresFolderRepository(session)

        folder = await repo.get_or_create_path(test_vault.id, "A/B/C")
        await session.commit()

        assert folder.path == "A/B/C"
        assert folder.depth == 2

        # Parent folders should also exist
        parent = await repo.get_by_path(test_vault.id, "A/B")
        assert parent is not None

        root = await repo.get_by_path(test_vault.id, "A")
        assert root is not None


@pytest.mark.integration
class TestTagRepository:
    """Tests for PostgresTagRepository."""

    @pytest.mark.asyncio
    async def test_create_tag(self, session: AsyncSession, test_vault: Vault):
        """Test creating a tag."""
        repo = PostgresTagRepository(session)

        tag = Tag(
            vault_id=test_vault.id,
            name="project",
            slug="project",
        )

        created = await repo.create(tag)
        await session.commit()

        assert created.id is not None
        assert created.name == "project"

    @pytest.mark.asyncio
    async def test_get_or_create_tag(self, session: AsyncSession, test_vault: Vault):
        """Test getting or creating a tag."""
        repo = PostgresTagRepository(session)

        # First call creates
        tag1 = await repo.get_or_create(test_vault.id, "newtag")
        await session.commit()

        assert tag1 is not None

        # Second call returns existing
        tag2 = await repo.get_or_create(test_vault.id, "newtag")

        assert tag2.id == tag1.id

    @pytest.mark.asyncio
    async def test_list_tags_by_vault(self, session: AsyncSession, test_vault: Vault):
        """Test listing tags by vault."""
        repo = PostgresTagRepository(session)

        # Create multiple tags
        for name in ["tag1", "tag2", "tag3"]:
            await repo.get_or_create(test_vault.id, name)

        await session.commit()

        tags = await repo.list_by_vault(test_vault.id)

        assert len(tags) >= 3


@pytest.mark.integration
class TestDocumentLinkRepository:
    """Tests for PostgresDocumentLinkRepository."""

    @pytest_asyncio.fixture
    async def test_documents(
        self, session: AsyncSession, test_vault: Vault
    ) -> tuple[Document, Document]:
        """Create test documents."""
        folder_repo = PostgresFolderRepository(session)
        folder = await folder_repo.get_or_create_path(test_vault.id, "Notes")

        doc_repo = PostgresDocumentRepository(session)

        source = Document(
            vault_id=test_vault.id,
            folder_id=folder.id,
            title="Source",
            filename="source.md",
            path="Notes/source.md",
            content="# Source\n\nLink to [[Target]].",
            content_hash="source",
        )

        target = Document(
            vault_id=test_vault.id,
            folder_id=folder.id,
            title="Target",
            filename="target.md",
            path="Notes/target.md",
            content="# Target",
            content_hash="target",
        )

        source = await doc_repo.create(source)
        target = await doc_repo.create(target)
        await session.commit()

        return source, target

    @pytest.mark.asyncio
    async def test_create_link(
        self,
        session: AsyncSession,
        test_vault: Vault,
        test_documents: tuple[Document, Document],
    ):
        """Test creating a document link."""
        source, target = test_documents
        repo = PostgresDocumentLinkRepository(session)

        link = DocumentLink(
            vault_id=test_vault.id,
            source_document_id=source.id,
            target_document_id=target.id,
            link_text="Target",
            link_type="wikilink",
            is_resolved=True,
        )

        created = await repo.create(link)
        await session.commit()

        assert created.id is not None
        assert created.is_resolved is True

    @pytest.mark.asyncio
    async def test_get_outgoing_links(
        self,
        session: AsyncSession,
        test_vault: Vault,
        test_documents: tuple[Document, Document],
    ):
        """Test getting outgoing links from a document."""
        source, target = test_documents
        repo = PostgresDocumentLinkRepository(session)

        link = DocumentLink(
            vault_id=test_vault.id,
            source_document_id=source.id,
            target_document_id=target.id,
            link_text="Target",
            link_type="wikilink",
            is_resolved=True,
        )
        await repo.create(link)
        await session.commit()

        links = await repo.get_outgoing_links(source.id)

        assert len(links) >= 1
        assert any(l.target_document_id == target.id for l in links)

    @pytest.mark.asyncio
    async def test_get_incoming_links(
        self,
        session: AsyncSession,
        test_vault: Vault,
        test_documents: tuple[Document, Document],
    ):
        """Test getting incoming links (backlinks) to a document."""
        source, target = test_documents
        repo = PostgresDocumentLinkRepository(session)

        link = DocumentLink(
            vault_id=test_vault.id,
            source_document_id=source.id,
            target_document_id=target.id,
            link_text="Target",
            link_type="wikilink",
            is_resolved=True,
        )
        await repo.create(link)
        await session.commit()

        backlinks = await repo.get_incoming_links(target.id)

        assert len(backlinks) >= 1

    @pytest.mark.asyncio
    async def test_delete_links_by_source(
        self,
        session: AsyncSession,
        test_vault: Vault,
        test_documents: tuple[Document, Document],
    ):
        """Test deleting all links from a source document."""
        source, target = test_documents
        repo = PostgresDocumentLinkRepository(session)

        link = DocumentLink(
            vault_id=test_vault.id,
            source_document_id=source.id,
            target_document_id=target.id,
            link_text="Target",
            link_type="wikilink",
            is_resolved=True,
        )
        await repo.create(link)
        await session.commit()

        await repo.delete_by_source(source.id)
        await session.commit()

        links = await repo.get_outgoing_links(source.id)
        assert len(links) == 0
