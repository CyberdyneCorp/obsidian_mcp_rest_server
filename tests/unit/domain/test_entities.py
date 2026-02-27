"""Tests for domain entities."""

from datetime import datetime
from uuid import uuid4

import pytest

from app.domain.entities.user import User
from app.domain.entities.vault import Vault
from app.domain.entities.document import Document
from app.domain.entities.folder import Folder
from app.domain.entities.tag import Tag
from app.domain.entities.document_link import DocumentLink
from app.domain.entities.embedding_chunk import EmbeddingChunk
from app.domain.value_objects.frontmatter import Frontmatter


class TestUser:
    """Tests for User entity."""

    def test_create_user(self):
        """Test creating a user with required fields."""
        user = User(
            email="test@example.com",
            password_hash="hashed",
            display_name="Test User",
        )

        assert user.email == "test@example.com"
        assert user.password_hash == "hashed"
        assert user.display_name == "Test User"
        assert user.is_active is True
        assert user.id is not None
        assert user.created_at is not None
        assert user.last_login_at is None

    def test_create_user_with_id(self):
        """Test creating a user with a specific ID."""
        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            password_hash="hashed",
            display_name="Test User",
        )

        assert user.id == user_id

    def test_update_last_login(self):
        """Test updating last login timestamp."""
        user = User(
            email="test@example.com",
            password_hash="hashed",
            display_name="Test User",
        )

        assert user.last_login_at is None
        user.update_last_login()
        assert user.last_login_at is not None
        assert isinstance(user.last_login_at, datetime)


class TestVault:
    """Tests for Vault entity."""

    def test_create_vault(self):
        """Test creating a vault."""
        user_id = uuid4()
        vault = Vault(
            user_id=user_id,
            name="My Vault",
            slug="my-vault",
        )

        assert vault.user_id == user_id
        assert vault.name == "My Vault"
        assert vault.slug == "my-vault"
        assert vault.description is None
        assert vault.document_count == 0
        assert vault.id is not None

    def test_create_vault_with_description(self):
        """Test creating a vault with description."""
        vault = Vault(
            user_id=uuid4(),
            name="My Vault",
            slug="my-vault",
            description="A test vault",
        )

        assert vault.description == "A test vault"

    def test_increment_document_count(self):
        """Test incrementing document count."""
        vault = Vault(
            user_id=uuid4(),
            name="My Vault",
            slug="my-vault",
        )

        assert vault.document_count == 0
        vault.increment_document_count()
        assert vault.document_count == 1
        vault.increment_document_count()
        assert vault.document_count == 2

    def test_decrement_document_count(self):
        """Test decrementing document count."""
        vault = Vault(
            user_id=uuid4(),
            name="My Vault",
            slug="my-vault",
            document_count=5,
        )

        vault.decrement_document_count()
        assert vault.document_count == 4

    def test_decrement_document_count_floor(self):
        """Test that document count cannot go below zero."""
        vault = Vault(
            user_id=uuid4(),
            name="My Vault",
            slug="my-vault",
            document_count=0,
        )

        vault.decrement_document_count()
        assert vault.document_count == 0


class TestDocument:
    """Tests for Document entity."""

    def test_create_document_with_factory(self):
        """Test creating a document using factory method."""
        vault_id = uuid4()

        doc = Document.create(
            vault_id=vault_id,
            path="Notes/test.md",
            content="# Test\n\nContent here.",
        )

        assert doc.vault_id == vault_id
        assert doc.title == "test"
        assert doc.filename == "test.md"
        assert doc.path == "Notes/test.md"
        assert doc.content == "# Test\n\nContent here."
        assert doc.content_hash != ""
        assert doc.word_count > 0

    def test_create_document_with_frontmatter(self):
        """Test creating a document with frontmatter."""
        fm = Frontmatter(
            title="Custom Title",
            tags=("test", "example"),
            aliases=("Test", "Testing"),
        )

        doc = Document.create(
            vault_id=uuid4(),
            path="Notes/test.md",
            content="# Test",
            frontmatter=fm,
        )

        assert doc.title == "Custom Title"
        assert doc.frontmatter.title == "Custom Title"
        assert "Test" in doc.aliases
        assert "Testing" in doc.aliases

    def test_update_content(self):
        """Test updating document content."""
        doc = Document.create(
            vault_id=uuid4(),
            path="test.md",
            content="Old content",
        )

        old_hash = doc.content_hash
        doc.update_content("New content")

        assert doc.content == "New content"
        assert doc.content_hash != old_hash
        assert doc.updated_at is not None

    def test_set_link_count(self):
        """Test setting link counts."""
        doc = Document.create(
            vault_id=uuid4(),
            path="test.md",
            content="Content",
        )

        doc.set_link_count(5)
        assert doc.link_count == 5

        doc.set_backlink_count(3)
        assert doc.backlink_count == 3

    def test_increment_decrement_backlinks(self):
        """Test incrementing and decrementing backlink count."""
        doc = Document.create(
            vault_id=uuid4(),
            path="test.md",
            content="Content",
        )

        doc.increment_backlink_count()
        assert doc.backlink_count == 1

        doc.increment_backlink_count(2)
        assert doc.backlink_count == 3

        doc.decrement_backlink_count()
        assert doc.backlink_count == 2

    def test_has_changed(self):
        """Test checking if content has changed."""
        doc = Document.create(
            vault_id=uuid4(),
            path="test.md",
            content="Original content",
        )

        assert doc.has_changed("Different content") is True
        assert doc.has_changed("Original content") is False

    def test_folder_path(self):
        """Test getting folder path from document."""
        doc = Document.create(
            vault_id=uuid4(),
            path="Notes/Projects/doc.md",
            content="Content",
        )

        assert doc.folder_path == "Notes/Projects"

        root_doc = Document.create(
            vault_id=uuid4(),
            path="doc.md",
            content="Content",
        )

        assert root_doc.folder_path is None


class TestFolder:
    """Tests for Folder entity."""

    def test_create_root_folder(self):
        """Test creating a root folder."""
        vault_id = uuid4()
        folder = Folder(
            vault_id=vault_id,
            parent_id=None,
            name="Notes",
            path="Notes",
            depth=0,
        )

        assert folder.vault_id == vault_id
        assert folder.parent_id is None
        assert folder.name == "Notes"
        assert folder.path == "Notes"
        assert folder.depth == 0

    def test_create_nested_folder(self):
        """Test creating a nested folder."""
        vault_id = uuid4()
        parent_id = uuid4()

        folder = Folder(
            vault_id=vault_id,
            parent_id=parent_id,
            name="Projects",
            path="Notes/Projects",
            depth=1,
        )

        assert folder.parent_id == parent_id
        assert folder.depth == 1
        assert folder.path == "Notes/Projects"


class TestTag:
    """Tests for Tag entity."""

    def test_create_simple_tag(self):
        """Test creating a simple tag."""
        vault_id = uuid4()
        tag = Tag(
            vault_id=vault_id,
            name="project",
            slug="project",
        )

        assert tag.vault_id == vault_id
        assert tag.name == "project"
        assert tag.slug == "project"
        assert tag.parent_tag_id is None
        assert tag.document_count == 0

    def test_create_nested_tag(self):
        """Test creating a nested tag."""
        vault_id = uuid4()
        parent_id = uuid4()

        tag = Tag(
            vault_id=vault_id,
            name="project/active",
            slug="project-active",
            parent_tag_id=parent_id,
        )

        assert tag.parent_tag_id == parent_id
        assert tag.name == "project/active"

    def test_increment_document_count(self):
        """Test incrementing document count."""
        tag = Tag(
            vault_id=uuid4(),
            name="test",
            slug="test",
        )

        tag.increment_document_count()
        assert tag.document_count == 1

    def test_decrement_document_count(self):
        """Test decrementing document count."""
        tag = Tag(
            vault_id=uuid4(),
            name="test",
            slug="test",
            document_count=5,
        )

        tag.decrement_document_count()
        assert tag.document_count == 4

    def test_decrement_document_count_floor(self):
        """Test that count cannot go below zero."""
        tag = Tag(
            vault_id=uuid4(),
            name="test",
            slug="test",
            document_count=0,
        )

        tag.decrement_document_count()
        assert tag.document_count == 0


class TestDocumentLink:
    """Tests for DocumentLink entity."""

    def test_create_unresolved_link(self):
        """Test creating an unresolved wiki-link."""
        vault_id = uuid4()
        source_id = uuid4()

        link = DocumentLink(
            vault_id=vault_id,
            source_document_id=source_id,
            target_document_id=None,
            link_text="Missing Note",
            link_type="wikilink",
            is_resolved=False,
        )

        assert link.vault_id == vault_id
        assert link.source_document_id == source_id
        assert link.target_document_id is None
        assert link.link_text == "Missing Note"
        assert link.link_type == "wikilink"
        assert link.is_resolved is False

    def test_create_resolved_link(self):
        """Test creating a resolved wiki-link."""
        vault_id = uuid4()
        source_id = uuid4()
        target_id = uuid4()

        link = DocumentLink(
            vault_id=vault_id,
            source_document_id=source_id,
            target_document_id=target_id,
            link_text="Existing Note",
            display_text="My Note",
            link_type="wikilink",
            is_resolved=True,
            position_start=100,
        )

        assert link.target_document_id == target_id
        assert link.display_text == "My Note"
        assert link.is_resolved is True
        assert link.position_start == 100

    def test_resolve_link(self):
        """Test resolving a link to a target document."""
        link = DocumentLink(
            vault_id=uuid4(),
            source_document_id=uuid4(),
            target_document_id=None,
            link_text="Target",
            link_type="wikilink",
            is_resolved=False,
        )

        target_id = uuid4()
        link.resolve(target_id)

        assert link.target_document_id == target_id
        assert link.is_resolved is True

    def test_link_types(self):
        """Test different link types."""
        vault_id = uuid4()
        source_id = uuid4()

        # Embed link
        embed_link = DocumentLink(
            vault_id=vault_id,
            source_document_id=source_id,
            link_text="image.png",
            link_type="embed",
            is_resolved=False,
        )
        assert embed_link.link_type == "embed"

        # Header link
        header_link = DocumentLink(
            vault_id=vault_id,
            source_document_id=source_id,
            link_text="Document#Section",
            link_type="header",
            is_resolved=False,
        )
        assert header_link.link_type == "header"

        # Block link
        block_link = DocumentLink(
            vault_id=vault_id,
            source_document_id=source_id,
            link_text="Document#^block-id",
            link_type="block",
            is_resolved=False,
        )
        assert block_link.link_type == "block"


class TestEmbeddingChunk:
    """Tests for EmbeddingChunk entity."""

    def test_create_embedding_chunk(self):
        """Test creating an embedding chunk."""
        vault_id = uuid4()
        document_id = uuid4()
        embedding = [0.1] * 1536

        chunk = EmbeddingChunk(
            vault_id=vault_id,
            document_id=document_id,
            chunk_index=0,
            content="This is a test chunk of text.",
            token_count=8,
            embedding=embedding,
        )

        assert chunk.vault_id == vault_id
        assert chunk.document_id == document_id
        assert chunk.chunk_index == 0
        assert chunk.content == "This is a test chunk of text."
        assert chunk.token_count == 8
        assert chunk.embedding == embedding
        assert len(chunk.embedding) == 1536

    def test_create_multiple_chunks(self):
        """Test creating multiple chunks for a document."""
        vault_id = uuid4()
        document_id = uuid4()

        chunks = [
            EmbeddingChunk(
                vault_id=vault_id,
                document_id=document_id,
                chunk_index=i,
                content=f"Chunk {i} content",
                token_count=3,
                embedding=[0.1 * i] * 1536,
            )
            for i in range(3)
        ]

        assert len(chunks) == 3
        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1
        assert chunks[2].chunk_index == 2
