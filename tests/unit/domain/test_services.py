"""Tests for domain services."""

from uuid import uuid4

import pytest

from app.domain.services.markdown_processor import MarkdownProcessor, ParsedDocument
from app.domain.services.link_resolver import LinkResolver
from app.domain.services.tag_parser import TagParser
from app.domain.entities.document import Document
from app.domain.value_objects.wiki_link import WikiLink
from app.domain.value_objects.frontmatter import Frontmatter


class TestMarkdownProcessor:
    """Tests for MarkdownProcessor service."""

    def test_extract_frontmatter(self):
        """Test extracting YAML frontmatter."""
        content = """---
title: Test Document
tags:
  - test
  - example
---

# Content

Body text here."""

        processor = MarkdownProcessor()
        frontmatter, body = processor.extract_frontmatter(content)

        assert frontmatter.title == "Test Document"
        assert "test" in frontmatter.tags
        assert "example" in frontmatter.tags
        assert "# Content" in body

    def test_extract_frontmatter_empty(self):
        """Test extracting from content without frontmatter."""
        content = "# Just a heading\n\nSome content."

        processor = MarkdownProcessor()
        frontmatter, body = processor.extract_frontmatter(content)

        assert frontmatter.title is None
        assert frontmatter.tags == ()
        assert "Just a heading" in body

    def test_extract_links(self):
        """Test extracting wiki-links from content."""
        content = """# Document

Here is a [[Simple Link]] and [[Target|Display Text]].

Also an embed ![[image.png]] and header link [[Note#Section]].
"""

        processor = MarkdownProcessor()
        links = processor.extract_links(content)

        assert len(links) == 4

        targets = [l.target for l in links]
        assert "Simple Link" in targets
        assert "Target" in targets
        assert "image.png" in targets
        assert "Note" in targets

    def test_extract_links_with_aliases(self):
        """Test wiki-links with display text."""
        content = "See [[Target|Display Text]] for more."

        processor = MarkdownProcessor()
        links = processor.extract_links(content)

        assert len(links) == 1
        assert links[0].target == "Target"
        assert links[0].display_text == "Display Text"

    def test_extract_embed_links(self):
        """Test embed links are flagged."""
        content = "An image: ![[photo.png]]"

        processor = MarkdownProcessor()
        links = processor.extract_links(content)

        assert len(links) == 1
        assert links[0].target == "photo.png"
        assert links[0].is_embed is True

    def test_extract_tags(self):
        """Test extracting inline tags."""
        # Note: tag parser doesn't support dashes, only letters, numbers, underscores, and /
        content = """# Document

This has #simple_tag and #nested/tag/here.

More text with #another_tag.
"""

        processor = MarkdownProcessor()
        tags = processor.extract_tags(content)

        assert "#simple_tag" in tags or "simple_tag" in " ".join(tags)
        assert any("nested" in t for t in tags)
        assert any("another" in t for t in tags)

    def test_count_words(self):
        """Test word counting."""
        content = """# Heading

This is a paragraph with several words.

- List item one
- List item two

Another paragraph here.
"""

        processor = MarkdownProcessor()
        count = processor.count_words(content)

        # Should count actual words, not markdown syntax
        assert count > 10
        assert count < 50

    def test_parse_complete_document(self):
        """Test full document parsing."""
        content = """---
title: Test Document
tags:
  - test
  - example
aliases:
  - Test
---

# Test Document

This is a [[Link]] to another document.

#inline-tag
"""

        processor = MarkdownProcessor()
        result = processor.parse(content)

        assert isinstance(result, ParsedDocument)
        assert result.frontmatter.title == "Test Document"
        assert "test" in result.frontmatter.tags
        assert len(result.links) == 1
        assert result.word_count > 0

    def test_get_heading(self):
        """Test extracting first heading."""
        content = """# My Document Title

Some content here.

## Another Heading
"""

        processor = MarkdownProcessor()
        heading = processor.get_heading(content)

        assert heading == "My Document Title"

    def test_get_excerpt(self):
        """Test getting content excerpt."""
        content = """# Title

This is the first paragraph of the document.

This is another paragraph with more content.
"""

        processor = MarkdownProcessor()
        excerpt = processor.get_excerpt(content, max_length=50)

        assert len(excerpt) <= 53  # 50 + "..."
        assert "first paragraph" in excerpt


class TestLinkResolver:
    """Tests for LinkResolver service."""

    def test_resolve_by_title(self):
        """Test resolving link by exact title match."""
        documents = [
            Document.create(
                vault_id=uuid4(),
                path="Notes/My Document.md",
                content="# My Document",
            ),
            Document.create(
                vault_id=uuid4(),
                path="Projects/Other.md",
                content="# Other",
            ),
        ]

        resolver = LinkResolver()
        link = WikiLink.parse("[[My Document]]")
        doc = resolver.resolve(link, documents)

        assert doc is not None
        assert doc.title == "My Document"

    def test_resolve_by_alias(self):
        """Test resolving link by alias."""
        fm = Frontmatter(aliases=("Doc", "My Doc"))
        documents = [
            Document.create(
                vault_id=uuid4(),
                path="Notes/Document.md",
                content="# Document",
                frontmatter=fm,
            ),
        ]

        resolver = LinkResolver()
        link = WikiLink.parse("[[Doc]]")
        doc = resolver.resolve(link, documents)

        assert doc is not None
        assert doc.title == "Document"

    def test_resolve_by_filename(self):
        """Test resolving link by filename."""
        documents = [
            Document.create(
                vault_id=uuid4(),
                path="Notes/my-document.md",
                content="# Different Title",
            ),
        ]

        resolver = LinkResolver()
        link = WikiLink.parse("[[my-document]]")
        doc = resolver.resolve(link, documents)

        assert doc is not None

    def test_resolve_case_insensitive(self):
        """Test case-insensitive resolution."""
        documents = [
            Document.create(
                vault_id=uuid4(),
                path="Notes/My Document.md",
                content="# My Document",
            ),
        ]

        resolver = LinkResolver()
        link = WikiLink.parse("[[my document]]")
        doc = resolver.resolve(link, documents)

        assert doc is not None

    def test_resolve_unmatched_returns_none(self):
        """Test unresolved link returns None."""
        documents = [
            Document.create(
                vault_id=uuid4(),
                path="Notes/Existing.md",
                content="# Existing",
            ),
        ]

        resolver = LinkResolver()
        link = WikiLink.parse("[[Nonexistent]]")
        doc = resolver.resolve(link, documents)

        assert doc is None

    def test_resolve_all(self):
        """Test resolving multiple links."""
        documents = [
            Document.create(
                vault_id=uuid4(),
                path="Doc A.md",
                content="# Doc A",
            ),
            Document.create(
                vault_id=uuid4(),
                path="Doc B.md",
                content="# Doc B",
            ),
        ]

        links = [
            WikiLink.parse("[[Doc A]]"),
            WikiLink.parse("[[Doc B]]"),
            WikiLink.parse("[[Nonexistent]]"),
        ]

        resolver = LinkResolver()
        results = resolver.resolve_all(links, documents)

        assert len(results) == 3
        assert results[links[0]] is not None
        assert results[links[1]] is not None
        assert results[links[2]] is None

    def test_find_matching_documents(self):
        """Test finding documents by partial match."""
        documents = [
            Document.create(
                vault_id=uuid4(),
                path="Project Alpha.md",
                content="# Project Alpha",
            ),
            Document.create(
                vault_id=uuid4(),
                path="Project Beta.md",
                content="# Project Beta",
            ),
            Document.create(
                vault_id=uuid4(),
                path="Notes.md",
                content="# Notes",
            ),
        ]

        resolver = LinkResolver()
        matches = resolver.find_matching_documents("Project", documents)

        assert len(matches) == 2


class TestTagParser:
    """Tests for TagParser service."""

    def test_extract_inline_tags(self):
        """Test extracting inline tags."""
        content = """
        This has #tag1 and #nested/tag2.
        Also #tag3 at the end.
        """

        parser = TagParser()
        tags = parser.extract_inline_tags(content)

        assert "#tag1" in tags
        assert "#nested/tag2" in tags
        assert "#tag3" in tags

    def test_extract_tags_deduplicates(self):
        """Test that duplicate tags are removed."""
        content = """
        #duplicate here
        and #duplicate again
        """

        parser = TagParser()
        tags = parser.extract_inline_tags(content)

        assert tags.count("#duplicate") == 1

    def test_parse_hierarchical_tag(self):
        """Test parsing hierarchical tag into parents."""
        parser = TagParser()

        hierarchy = parser.parse_hierarchical_tag("#project/active/urgent")

        assert hierarchy == ["#project", "#project/active", "#project/active/urgent"]

    def test_normalize_tag(self):
        """Test tag normalization."""
        parser = TagParser()

        assert parser.normalize_tag("TAG") == "#tag"
        assert parser.normalize_tag("#Tag") == "#tag"
        assert parser.normalize_tag("  tag  ") == "#tag"

    def test_is_valid_tag(self):
        """Test tag validation."""
        parser = TagParser()

        assert parser.is_valid_tag("project") is True
        assert parser.is_valid_tag("#project") is True
        assert parser.is_valid_tag("nested/tag") is True
        assert parser.is_valid_tag("tag-with-dash") is False  # dash not allowed
        assert parser.is_valid_tag("tag_with_underscore") is True
        assert parser.is_valid_tag("123numeric") is False  # must start with letter
        assert parser.is_valid_tag("") is False
        assert parser.is_valid_tag("tag//double") is False  # no double slashes

    def test_get_tag_depth(self):
        """Test getting tag depth."""
        parser = TagParser()

        assert parser.get_tag_depth("#project") == 0
        assert parser.get_tag_depth("#project/active") == 1
        assert parser.get_tag_depth("#project/active/urgent") == 2

    def test_get_parent_tag(self):
        """Test getting parent tag."""
        parser = TagParser()

        assert parser.get_parent_tag("#project") is None
        assert parser.get_parent_tag("#project/active") == "#project"
        assert parser.get_parent_tag("#project/active/urgent") == "#project/active"

    def test_get_root_tag(self):
        """Test getting root tag."""
        parser = TagParser()

        assert parser.get_root_tag("#project") == "#project"
        assert parser.get_root_tag("#project/active/urgent") == "#project"

    def test_merge_tags(self):
        """Test merging frontmatter and inline tags."""
        parser = TagParser()

        frontmatter_tags = ["project", "important"]
        inline_tags = ["#status/active", "#project"]  # project is duplicate

        merged = parser.merge_tags(frontmatter_tags, inline_tags)

        # Should have unique normalized tags
        assert "#project" in merged
        assert "#important" in merged
        assert "#status/active" in merged
        # No duplicates
        assert len([t for t in merged if "project" in t and "/" not in t]) == 1

    def test_expand_hierarchical_tags(self):
        """Test expanding hierarchical tags."""
        parser = TagParser()

        tags = ["#project/active"]
        expanded = parser.expand_hierarchical_tags(tags)

        assert "#project" in expanded
        assert "#project/active" in expanded
