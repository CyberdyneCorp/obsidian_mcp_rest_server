"""Pytest configuration and shared fixtures."""

from uuid import uuid4

import pytest

from app.domain.entities.user import User
from app.domain.entities.vault import Vault
from app.domain.entities.document import Document
from app.domain.entities.folder import Folder
from app.domain.entities.tag import Tag
from app.domain.entities.document_link import DocumentLink
from app.domain.entities.embedding_chunk import EmbeddingChunk


# Sample data fixtures
@pytest.fixture
def sample_user() -> User:
    """Create a sample user."""
    return User(
        id=uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        display_name="Test User",
        is_active=True,
    )


@pytest.fixture
def sample_vault(sample_user: User) -> Vault:
    """Create a sample vault."""
    return Vault(
        id=uuid4(),
        user_id=sample_user.id,
        name="My Knowledge Base",
        slug="my-knowledge-base",
        description="A test vault for knowledge management",
        document_count=0,
    )


@pytest.fixture
def sample_folder(sample_vault: Vault) -> Folder:
    """Create a sample folder."""
    return Folder(
        id=uuid4(),
        vault_id=sample_vault.id,
        parent_id=None,
        name="Notes",
        path="Notes",
        depth=0,
    )


@pytest.fixture
def sample_document(sample_vault: Vault, sample_folder: Folder) -> Document:
    """Create a sample document."""
    return Document(
        id=uuid4(),
        vault_id=sample_vault.id,
        folder_id=sample_folder.id,
        title="Getting Started",
        filename="Getting Started.md",
        path="Notes/Getting Started.md",
        content="# Getting Started\n\nWelcome to my knowledge base!\n\nSee also [[Other Note]].",
        content_hash="abc123",
        frontmatter={"tags": ["welcome", "intro"]},
        aliases=["start", "intro"],
        word_count=10,
        link_count=1,
        backlink_count=0,
    )


@pytest.fixture
def sample_document_with_links(sample_vault: Vault, sample_folder: Folder) -> Document:
    """Create a sample document with various link types."""
    content = """---
tags:
  - project
  - planning
aliases:
  - Project Overview
---

# Project Planning

This document links to [[Meeting Notes]] and [[Tasks/Todo List|Todo]].

We also embed ![[Architecture Diagram.png]].

See the #project/planning section for more details.

Reference [[Notes/Reference#Section One]] for the header link.
"""
    return Document(
        id=uuid4(),
        vault_id=sample_vault.id,
        folder_id=sample_folder.id,
        title="Project Planning",
        filename="Project Planning.md",
        path="Notes/Project Planning.md",
        content=content,
        content_hash="def456",
        frontmatter={"tags": ["project", "planning"], "aliases": ["Project Overview"]},
        aliases=["Project Overview"],
        word_count=30,
        link_count=4,
        backlink_count=0,
    )


@pytest.fixture
def sample_tag(sample_vault: Vault) -> Tag:
    """Create a sample tag."""
    return Tag(
        id=uuid4(),
        vault_id=sample_vault.id,
        name="project",
        slug="project",
        parent_tag_id=None,
        document_count=1,
    )


@pytest.fixture
def sample_nested_tag(sample_vault: Vault, sample_tag: Tag) -> Tag:
    """Create a nested tag."""
    return Tag(
        id=uuid4(),
        vault_id=sample_vault.id,
        name="project/planning",
        slug="project-planning",
        parent_tag_id=sample_tag.id,
        document_count=1,
    )


@pytest.fixture
def sample_document_link(
    sample_vault: Vault,
    sample_document: Document,
) -> DocumentLink:
    """Create a sample document link."""
    return DocumentLink(
        id=uuid4(),
        vault_id=sample_vault.id,
        source_document_id=sample_document.id,
        target_document_id=None,  # Unresolved
        link_text="Other Note",
        display_text=None,
        link_type="wikilink",
        is_resolved=False,
        position_start=70,
    )


@pytest.fixture
def sample_embedding_chunk(
    sample_vault: Vault,
    sample_document: Document,
) -> EmbeddingChunk:
    """Create a sample embedding chunk."""
    return EmbeddingChunk(
        id=uuid4(),
        vault_id=sample_vault.id,
        document_id=sample_document.id,
        chunk_index=0,
        content="Welcome to my knowledge base!",
        token_count=6,
        embedding=[0.1] * 1536,  # Dummy embedding
    )


# Markdown content fixtures
@pytest.fixture
def markdown_with_frontmatter() -> str:
    """Sample markdown with YAML frontmatter."""
    return """---
title: Test Document
tags:
  - test
  - example
aliases:
  - Test
  - Sample
date: 2024-01-15
custom_field: custom_value
---

# Test Document

This is the content of the document.
"""


@pytest.fixture
def markdown_with_links() -> str:
    """Sample markdown with various link types."""
    return """# Document with Links

Here is a [[simple link]].
And a [[target|display text]] with alias.
An embed: ![[image.png]]
A header link: [[Document#Section]]
A block link: [[Document#^block-id]]
An external link: [Google](https://google.com)
"""


@pytest.fixture
def markdown_with_tags() -> str:
    """Sample markdown with inline tags."""
    return """# Document with Tags

This document has #simple-tag and #nested/tag/here.
Also #another-tag at the end.

Code block should be ignored:
```python
#not-a-tag
```
"""


# ZIP content fixtures
@pytest.fixture
def sample_vault_zip() -> bytes:
    """Create a sample vault ZIP file."""
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Root document
        zf.writestr(
            "Welcome.md",
            """---
tags: [welcome]
---

# Welcome

This is the welcome page. See [[Notes/Getting Started]].
""",
        )

        # Notes folder
        zf.writestr(
            "Notes/Getting Started.md",
            """---
tags: [intro, guide]
aliases: [Start Here]
---

# Getting Started

Welcome to the vault! Check out [[Projects/Project A]].

#getting-started
""",
        )

        zf.writestr(
            "Notes/Reference.md",
            """# Reference

Some reference material.

## Section One

Content for section one.

## Section Two

Content for section two.
""",
        )

        # Projects folder
        zf.writestr(
            "Projects/Project A.md",
            """---
status: active
tags: [project]
---

# Project A

This is an active project.

See also:
- [[Notes/Getting Started|Getting Started Guide]]
- [[Notes/Reference#Section One]]
""",
        )

        # Attachments
        zf.writestr("Attachments/diagram.png", b"fake png content")

    buffer.seek(0)
    return buffer.read()
