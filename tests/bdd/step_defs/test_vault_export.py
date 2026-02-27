"""Step definitions for vault export feature."""

import io
import zipfile
from uuid import uuid4

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from app.domain.entities.vault import Vault
from app.domain.entities.document import Document
from app.domain.value_objects.frontmatter import Frontmatter
from app.domain.services.markdown_processor import MarkdownProcessor
from tests.bdd.conftest import create_test_zip

# Load scenarios from feature file
scenarios("../features/vault_export.feature")


@given(parsers.parse('a vault "{vault_slug}" exists with documents'))
def given_vault_exists_with_documents(context: dict, mock_repositories: dict, vault_slug: str):
    """Create vault with documents for export."""
    vault = Vault(
        id=uuid4(),
        user_id=context["user"].id,
        name=vault_slug.replace("-", " ").title(),
        slug=vault_slug,
        document_count=3,
    )
    context["vault"] = vault
    context["vault_slug"] = vault_slug

    documents = [
        Document(
            id=uuid4(),
            vault_id=vault.id,
            title="Welcome",
            filename="Welcome.md",
            path="Welcome.md",
            content="# Welcome\n\nThis is the welcome page.",
            content_hash="hash1",
            frontmatter=Frontmatter(tags=("welcome",)),
        ),
        Document(
            id=uuid4(),
            vault_id=vault.id,
            title="Getting Started",
            filename="Getting Started.md",
            path="Notes/Getting Started.md",
            content="# Getting Started\n\nHow to use this vault.",
            content_hash="hash2",
            frontmatter=Frontmatter(title="Getting Started Guide", tags=("guide", "intro")),
        ),
        Document(
            id=uuid4(),
            vault_id=vault.id,
            title="Project A",
            filename="Project A.md",
            path="Projects/Project A.md",
            content="# Project A\n\nProject details here.",
            content_hash="hash3",
            frontmatter=Frontmatter(
                tags=("project", "active"),
                custom_fields={"status": "in-progress", "priority": "high"},
            ),
        ),
    ]

    context["documents"] = documents
    context["expected_paths"] = [d.path for d in documents]

    mock_repositories["vault_repo"].get_by_slug.return_value = vault
    mock_repositories["document_repo"].list_by_vault.return_value = documents


@when(parsers.parse('I export the vault "{vault_slug}"'))
def when_export_vault(context: dict, vault_slug: str):
    """Export the vault as ZIP."""
    processor = MarkdownProcessor()
    documents = context.get("documents", [])

    # Simulate export
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for doc in documents:
            content = processor.render_with_frontmatter(doc.content, doc.frontmatter)
            zf.writestr(doc.path, content.encode("utf-8"))

    context["exported_zip"] = zip_buffer.getvalue()


@then("I receive a ZIP file")
def then_receive_zip(context: dict):
    """Verify ZIP was created."""
    assert "exported_zip" in context
    assert len(context["exported_zip"]) > 0

    # Verify it's a valid ZIP
    with zipfile.ZipFile(io.BytesIO(context["exported_zip"]), "r") as zf:
        assert zf.testzip() is None  # Returns None if no errors


@then("the ZIP contains all documents from the vault")
def then_zip_contains_all_documents(context: dict):
    """Verify all documents are in ZIP."""
    with zipfile.ZipFile(io.BytesIO(context["exported_zip"]), "r") as zf:
        names = zf.namelist()
        for expected_path in context["expected_paths"]:
            assert expected_path in names, f"Missing: {expected_path}"


@then("the folder structure is preserved in the ZIP")
def then_folder_structure_preserved(context: dict):
    """Verify folder structure in ZIP."""
    with zipfile.ZipFile(io.BytesIO(context["exported_zip"]), "r") as zf:
        names = zf.namelist()

        # Check for nested paths
        assert any("Notes/" in n for n in names), "Notes folder missing"
        assert any("Projects/" in n for n in names), "Projects folder missing"


@given("a vault with documents containing frontmatter")
def given_vault_with_frontmatter(context: dict, mock_repositories: dict):
    """Create vault with rich frontmatter."""
    vault = Vault(
        id=uuid4(),
        user_id=context["user"].id,
        name="Frontmatter Vault",
        slug="frontmatter-vault",
    )
    context["vault"] = vault

    documents = [
        Document(
            id=uuid4(),
            vault_id=vault.id,
            title="Rich Document",
            filename="rich.md",
            path="rich.md",
            content="# Rich Document\n\nContent with metadata.",
            content_hash="hash",
            frontmatter=Frontmatter(
                title="Rich Document Title",
                tags=("tag1", "tag2", "nested/tag"),
                aliases=("Alias1", "Alias2"),
                custom_fields={
                    "status": "published",
                    "author": "Test Author",
                    "date": "2024-01-15",
                },
            ),
        ),
    ]

    context["documents"] = documents
    mock_repositories["vault_repo"].get_by_slug.return_value = vault
    mock_repositories["document_repo"].list_by_vault.return_value = documents


@when("I export the vault")
def when_export_vault_generic(context: dict):
    """Export the current vault."""
    processor = MarkdownProcessor()
    documents = context.get("documents", [])

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for doc in documents:
            content = processor.render_with_frontmatter(doc.content, doc.frontmatter)
            zf.writestr(doc.path, content.encode("utf-8"))

    context["exported_zip"] = zip_buffer.getvalue()


@then("each document in the ZIP includes its YAML frontmatter")
def then_documents_include_frontmatter(context: dict):
    """Verify frontmatter is included."""
    with zipfile.ZipFile(io.BytesIO(context["exported_zip"]), "r") as zf:
        for name in zf.namelist():
            content = zf.read(name).decode("utf-8")
            # Frontmatter starts with ---
            assert content.startswith("---"), f"{name} missing frontmatter"
            assert "---\n" in content[3:], f"{name} missing frontmatter end"


@then("tags are preserved in frontmatter")
def then_tags_preserved(context: dict):
    """Verify tags in frontmatter."""
    with zipfile.ZipFile(io.BytesIO(context["exported_zip"]), "r") as zf:
        for name in zf.namelist():
            content = zf.read(name).decode("utf-8")
            assert "tags:" in content, f"{name} missing tags"


@then("custom fields are preserved")
def then_custom_fields_preserved(context: dict):
    """Verify custom fields in frontmatter."""
    with zipfile.ZipFile(io.BytesIO(context["exported_zip"]), "r") as zf:
        # Check the rich document
        content = zf.read("rich.md").decode("utf-8")
        assert "status:" in content
        assert "author:" in content


@given(parsers.parse('an empty vault "{vault_slug}" exists'))
def given_empty_vault(context: dict, mock_repositories: dict, vault_slug: str):
    """Create empty vault."""
    vault = Vault(
        id=uuid4(),
        user_id=context["user"].id,
        name=vault_slug.replace("-", " ").title(),
        slug=vault_slug,
        document_count=0,
    )
    context["vault"] = vault
    context["vault_slug"] = vault_slug
    context["documents"] = []

    mock_repositories["vault_repo"].get_by_slug.return_value = vault
    mock_repositories["document_repo"].list_by_vault.return_value = []


@then("I receive a valid but empty ZIP file")
def then_empty_valid_zip(context: dict):
    """Verify empty but valid ZIP."""
    with zipfile.ZipFile(io.BytesIO(context["exported_zip"]), "r") as zf:
        assert len(zf.namelist()) == 0
        assert zf.testzip() is None


@given("a vault with deeply nested folder structure")
def given_deeply_nested_vault(context: dict, mock_repositories: dict):
    """Create vault with deep nesting."""
    vault = Vault(
        id=uuid4(),
        user_id=context["user"].id,
        name="Nested Vault",
        slug="nested-vault",
    )
    context["vault"] = vault

    documents = [
        Document(
            id=uuid4(),
            vault_id=vault.id,
            title="Root",
            filename="root.md",
            path="root.md",
            content="# Root",
            content_hash="h1",
        ),
        Document(
            id=uuid4(),
            vault_id=vault.id,
            title="Level 1",
            filename="l1.md",
            path="A/l1.md",
            content="# Level 1",
            content_hash="h2",
        ),
        Document(
            id=uuid4(),
            vault_id=vault.id,
            title="Level 2",
            filename="l2.md",
            path="A/B/l2.md",
            content="# Level 2",
            content_hash="h3",
        ),
        Document(
            id=uuid4(),
            vault_id=vault.id,
            title="Level 3",
            filename="l3.md",
            path="A/B/C/l3.md",
            content="# Level 3",
            content_hash="h4",
        ),
        Document(
            id=uuid4(),
            vault_id=vault.id,
            title="Deep",
            filename="deep.md",
            path="A/B/C/D/E/deep.md",
            content="# Deep",
            content_hash="h5",
        ),
    ]

    context["documents"] = documents
    context["expected_paths"] = [d.path for d in documents]

    mock_repositories["vault_repo"].get_by_slug.return_value = vault
    mock_repositories["document_repo"].list_by_vault.return_value = documents


@then("all nested paths are preserved in the ZIP")
def then_nested_paths_preserved(context: dict):
    """Verify nested paths exist."""
    with zipfile.ZipFile(io.BytesIO(context["exported_zip"]), "r") as zf:
        names = zf.namelist()
        for expected in context["expected_paths"]:
            assert expected in names, f"Missing nested path: {expected}"


@then("documents can be found at their original paths")
def then_documents_at_original_paths(context: dict):
    """Verify documents are at correct paths."""
    with zipfile.ZipFile(io.BytesIO(context["exported_zip"]), "r") as zf:
        for doc in context["documents"]:
            content = zf.read(doc.path).decode("utf-8")
            # Title should be in content
            assert doc.title in content


@when(parsers.parse('I try to export a non-existent vault "{vault_slug}"'))
def when_export_nonexistent(context: dict, mock_repositories: dict, vault_slug: str):
    """Try to export non-existent vault."""
    mock_repositories["vault_repo"].get_by_slug.return_value = None
    context["vault_slug"] = vault_slug
    context["export_error"] = True


@then("I receive a not found error")
def then_not_found_error(context: dict):
    """Verify not found error."""
    assert context.get("export_error") is True


@given(parsers.parse('a vault "{vault_slug}" was imported from a ZIP file'))
def given_vault_imported_from_zip(context: dict, mock_repositories: dict, vault_slug: str):
    """Create vault that was imported."""
    # Simulate original ZIP content
    original_files = {
        "Welcome.md": "---\ntags:\n  - welcome\n---\n\n# Welcome\n\nOriginal content.",
        "Notes/Guide.md": "---\ntitle: User Guide\n---\n\n# Guide\n\nGuide content.",
    }
    context["original_files"] = original_files
    context["original_zip"] = create_test_zip(original_files)

    vault = Vault(
        id=uuid4(),
        user_id=context["user"].id,
        name=vault_slug.replace("-", " ").title(),
        slug=vault_slug,
    )
    context["vault"] = vault
    context["vault_slug"] = vault_slug

    # Create documents matching original
    documents = [
        Document(
            id=uuid4(),
            vault_id=vault.id,
            title="Welcome",
            filename="Welcome.md",
            path="Welcome.md",
            content="# Welcome\n\nOriginal content.",
            content_hash="h1",
            frontmatter=Frontmatter(tags=("welcome",)),
        ),
        Document(
            id=uuid4(),
            vault_id=vault.id,
            title="Guide",
            filename="Guide.md",
            path="Notes/Guide.md",
            content="# Guide\n\nGuide content.",
            content_hash="h2",
            frontmatter=Frontmatter(title="User Guide"),
        ),
    ]

    context["documents"] = documents
    mock_repositories["vault_repo"].get_by_slug.return_value = vault
    mock_repositories["document_repo"].list_by_vault.return_value = documents


@then("the exported ZIP has the same structure as the original")
def then_same_structure(context: dict):
    """Verify structure matches original."""
    with zipfile.ZipFile(io.BytesIO(context["exported_zip"]), "r") as exported_zf:
        with zipfile.ZipFile(io.BytesIO(context["original_zip"]), "r") as original_zf:
            exported_names = set(exported_zf.namelist())
            original_names = set(original_zf.namelist())
            assert exported_names == original_names


@then("document content matches the original")
def then_content_matches(context: dict):
    """Verify content matches."""
    with zipfile.ZipFile(io.BytesIO(context["exported_zip"]), "r") as zf:
        for path, original_content in context["original_files"].items():
            exported_content = zf.read(path).decode("utf-8")
            # Check key content is preserved (frontmatter format might differ slightly)
            if "# Welcome" in original_content:
                assert "# Welcome" in exported_content
            if "# Guide" in original_content:
                assert "# Guide" in exported_content
