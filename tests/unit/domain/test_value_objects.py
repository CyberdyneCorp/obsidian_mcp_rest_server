"""Tests for domain value objects."""

import pytest

from app.domain.value_objects.wiki_link import WikiLink
from app.domain.value_objects.frontmatter import Frontmatter
from app.domain.value_objects.document_path import DocumentPath


class TestWikiLink:
    """Tests for WikiLink value object."""

    def test_parse_simple_link(self):
        """Test parsing a simple wiki-link."""
        link = WikiLink.parse("[[My Note]]")

        assert link.target == "My Note"
        assert link.display_text == "My Note"
        assert link.heading is None
        assert link.block_id is None
        assert link.is_embed is False

    def test_parse_link_with_alias(self):
        """Test parsing a wiki-link with display text."""
        link = WikiLink.parse("[[Target Note|Display Text]]")

        assert link.target == "Target Note"
        assert link.display_text == "Display Text"

    def test_parse_embed_link(self):
        """Test parsing an embed link."""
        link = WikiLink.parse("![[image.png]]")

        assert link.target == "image.png"
        assert link.is_embed is True

    def test_parse_link_with_heading(self):
        """Test parsing a link with heading reference."""
        link = WikiLink.parse("[[Note#Section One]]")

        assert link.target == "Note"
        assert link.heading == "Section One"

    def test_parse_link_with_block_id(self):
        """Test parsing a link with block ID."""
        link = WikiLink.parse("[[Note#^block-123]]")

        assert link.target == "Note"
        assert link.block_id == "block-123"
        assert link.heading is None

    def test_parse_link_with_path(self):
        """Test parsing a link with folder path."""
        link = WikiLink.parse("[[Folder/Subfolder/Note]]")

        assert link.target == "Folder/Subfolder/Note"

    def test_parse_complex_link(self):
        """Test parsing a complex link with path, heading, and alias."""
        link = WikiLink.parse("[[Projects/Active/Project A#Overview|Project Overview]]")

        assert link.target == "Projects/Active/Project A"
        assert link.heading == "Overview"
        assert link.display_text == "Project Overview"

    def test_parse_embed_with_heading(self):
        """Test parsing an embed with heading."""
        link = WikiLink.parse("![[Document#Section]]")

        assert link.target == "Document"
        assert link.heading == "Section"
        assert link.is_embed is True

    def test_to_markdown_simple(self):
        """Test converting simple link to markdown."""
        link = WikiLink(target="My Note", display_text="My Note")
        assert link.to_markdown() == "[[My Note]]"

    def test_to_markdown_with_alias(self):
        """Test converting link with alias to markdown."""
        link = WikiLink(target="Target", display_text="Display")
        assert link.to_markdown() == "[[Target|Display]]"

    def test_to_markdown_embed(self):
        """Test converting embed to markdown."""
        link = WikiLink(target="image.png", display_text="image.png", is_embed=True)
        assert link.to_markdown() == "![[image.png]]"

    def test_to_markdown_with_heading(self):
        """Test converting link with heading to markdown."""
        link = WikiLink(target="Note", display_text="Note", heading="Section")
        assert link.to_markdown() == "[[Note#Section]]"

    def test_equality(self):
        """Test WikiLink equality."""
        link1 = WikiLink(target="Note", display_text="Note")
        link2 = WikiLink(target="Note", display_text="Note")
        link3 = WikiLink(target="Other", display_text="Other")

        assert link1 == link2
        assert link1 != link3

    def test_hash(self):
        """Test WikiLink hashability."""
        link1 = WikiLink(target="Note", display_text="Note")
        link2 = WikiLink(target="Note", display_text="Note")

        links = {link1, link2}
        assert len(links) == 1


class TestFrontmatter:
    """Tests for Frontmatter value object."""

    def test_parse_simple_frontmatter(self):
        """Test parsing simple YAML frontmatter."""
        yaml_text = """title: Test Document
author: John Doe"""

        fm = Frontmatter.parse(yaml_text)

        assert fm.title == "Test Document"
        assert fm.custom_fields["author"] == "John Doe"

    def test_parse_frontmatter_with_tags(self):
        """Test parsing frontmatter with tags array."""
        yaml_text = """tags:
  - project
  - active
  - important"""

        fm = Frontmatter.parse(yaml_text)

        assert "project" in fm.tags
        assert "active" in fm.tags
        assert "important" in fm.tags

    def test_parse_frontmatter_with_aliases(self):
        """Test parsing frontmatter with aliases."""
        yaml_text = """aliases:
  - Alias One
  - Alias Two"""

        fm = Frontmatter.parse(yaml_text)

        assert "Alias One" in fm.aliases
        assert "Alias Two" in fm.aliases

    def test_parse_empty_frontmatter(self):
        """Test parsing empty frontmatter."""
        fm = Frontmatter.parse("")
        assert fm.title is None
        assert fm.tags == ()
        assert fm.aliases == ()

    def test_parse_complex_frontmatter(self):
        """Test parsing complex nested frontmatter."""
        yaml_text = """title: Complex Document
tags:
  - tag1
  - tag2
metadata:
  created: 2024-01-15
  status: draft"""

        fm = Frontmatter.parse(yaml_text)

        assert fm.title == "Complex Document"
        assert "tag1" in fm.tags
        assert fm.custom_fields["metadata"]["status"] == "draft"

    def test_to_yaml(self):
        """Test converting frontmatter to YAML string."""
        fm = Frontmatter(title="Test", tags=("a", "b"))
        yaml_str = fm.to_yaml()

        assert "title: Test" in yaml_str
        assert "tags:" in yaml_str

    def test_to_dict(self):
        """Test converting frontmatter to dictionary."""
        fm = Frontmatter(
            title="Test",
            tags=("tag1", "tag2"),
            aliases=("alias1",),
            custom_fields={"key": "value"},
        )
        data = fm.to_dict()

        assert data["title"] == "Test"
        assert data["tags"] == ["tag1", "tag2"]
        assert data["aliases"] == ["alias1"]
        assert data["key"] == "value"

    def test_from_dict(self):
        """Test creating frontmatter from dictionary."""
        data = {
            "title": "Test",
            "tags": ["a", "b"],
            "aliases": ["x"],
            "custom": "value",
        }
        fm = Frontmatter.from_dict(data)

        assert fm.title == "Test"
        assert "a" in fm.tags
        assert "x" in fm.aliases
        assert fm.custom_fields["custom"] == "value"

    def test_with_title(self):
        """Test creating new frontmatter with updated title."""
        fm = Frontmatter(title="Old")
        new_fm = fm.with_title("New")

        assert new_fm.title == "New"
        assert fm.title == "Old"  # Original unchanged

    def test_merge(self):
        """Test merging two frontmatter objects."""
        fm1 = Frontmatter(title="Title1", tags=("tag1",))
        fm2 = Frontmatter(title="Title2", tags=("tag2",))

        merged = fm1.merge(fm2)

        assert merged.title == "Title2"  # Other takes precedence
        assert "tag1" in merged.tags
        assert "tag2" in merged.tags


class TestDocumentPath:
    """Tests for DocumentPath value object."""

    def test_create_simple_path(self):
        """Test creating a simple document path."""
        path = DocumentPath("Notes/My Document.md")

        assert path.path == "Notes/My Document.md"
        assert path.filename == "My Document.md"
        assert path.folder_path == "Notes"
        assert path.title == "My Document"
        assert path.extension == "md"

    def test_create_root_path(self):
        """Test creating a path at root level."""
        path = DocumentPath("Document.md")

        assert path.path == "Document.md"
        assert path.filename == "Document.md"
        assert path.folder_path is None
        assert path.title == "Document"

    def test_create_nested_path(self):
        """Test creating a deeply nested path."""
        path = DocumentPath("Projects/2024/Q1/Planning.md")

        assert path.path == "Projects/2024/Q1/Planning.md"
        assert path.filename == "Planning.md"
        assert path.folder_path == "Projects/2024/Q1"
        assert path.title == "Planning"

    def test_path_with_spaces(self):
        """Test path with spaces in names."""
        path = DocumentPath("My Notes/Important Document.md")

        assert path.folder_path == "My Notes"
        assert path.title == "Important Document"

    def test_path_without_extension(self):
        """Test path without file extension."""
        path = DocumentPath("Notes/README")

        assert path.filename == "README"
        assert path.title == "README"
        assert path.extension is None

    def test_normalize_path(self):
        """Test path normalization."""
        # Remove leading/trailing slashes
        path = DocumentPath("/Notes/Document.md/")
        assert path.path == "Notes/Document.md"

        # Handle double slashes
        path = DocumentPath("Notes//Document.md")
        assert path.path == "Notes/Document.md"

    def test_parts(self):
        """Test getting path parts."""
        path = DocumentPath("A/B/C/Document.md")
        assert path.parts == ("A", "B", "C", "Document.md")

    def test_folder_parts(self):
        """Test getting folder parts."""
        path = DocumentPath("A/B/C/Document.md")
        assert path.folder_parts == ("A", "B", "C")

    def test_depth(self):
        """Test path depth."""
        assert DocumentPath("Document.md").depth == 0
        assert DocumentPath("A/Document.md").depth == 1
        assert DocumentPath("A/B/C/Document.md").depth == 3

    def test_is_under(self):
        """Test checking if path is under folder."""
        path = DocumentPath("Notes/Projects/Document.md")

        assert path.is_under("Notes")
        assert path.is_under("Notes/Projects")
        assert not path.is_under("Other")
        assert not path.is_under("Notes/Other")

    def test_is_markdown(self):
        """Test checking if file is markdown."""
        assert DocumentPath("doc.md").is_markdown is True
        assert DocumentPath("doc.MD").is_markdown is True
        assert DocumentPath("image.png").is_markdown is False

    def test_with_extension(self):
        """Test changing extension."""
        path = DocumentPath("Notes/doc.md")
        new_path = path.with_extension(".txt")

        assert new_path.path == "Notes/doc.txt"

    def test_in_folder(self):
        """Test moving to different folder."""
        path = DocumentPath("doc.md")
        new_path = path.in_folder("Notes/Projects")

        assert new_path.path == "Notes/Projects/doc.md"

    def test_relative_to(self):
        """Test getting relative path."""
        path = DocumentPath("Notes/Projects/doc.md")
        relative = path.relative_to("Notes")

        assert relative.path == "Projects/doc.md"

    def test_join(self):
        """Test joining path parts."""
        path = DocumentPath.join("Notes", "Projects", "doc.md")
        assert path.path == "Notes/Projects/doc.md"

    def test_equality(self):
        """Test DocumentPath equality."""
        path1 = DocumentPath("Notes/Doc.md")
        path2 = DocumentPath("Notes/Doc.md")
        path3 = DocumentPath("Other/Doc.md")

        assert path1 == path2
        assert path1 != path3

    def test_equality_case_insensitive(self):
        """Test case-insensitive equality."""
        path1 = DocumentPath("Notes/Doc.md")
        path2 = DocumentPath("notes/doc.md")

        assert path1 == path2

    def test_hash(self):
        """Test DocumentPath hashability."""
        path1 = DocumentPath("Notes/Doc.md")
        path2 = DocumentPath("Notes/Doc.md")

        paths = {path1, path2}
        assert len(paths) == 1

    def test_str_representation(self):
        """Test string representation."""
        path = DocumentPath("Notes/Document.md")
        assert str(path) == "Notes/Document.md"
