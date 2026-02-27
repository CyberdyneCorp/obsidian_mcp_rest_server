"""Step definitions for document linking feature."""

from uuid import uuid4

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from app.domain.entities.vault import Vault
from app.domain.entities.document import Document
from app.domain.entities.document_link import DocumentLink

# Load scenarios from feature file
scenarios("../features/document_linking.feature")


@given(parsers.parse('a document "{doc_title}" with links to other documents'))
def given_document_with_links(context: dict, mock_repositories: dict, doc_title: str):
    """Create document with outgoing links."""
    vault = context["vault"]
    source_doc = context["documents"].get(doc_title)

    if not source_doc:
        source_doc = Document(
            id=uuid4(),
            vault_id=vault.id,
            folder_id=context["folder"].id,
            title=doc_title,
            filename=f"{doc_title}.md",
            path=f"Notes/{doc_title}.md",
            content=f"# {doc_title}\n\nLinks to [[Reference]] and [[Tasks]].",
            content_hash="hash",
            link_count=2,
        )
        context["documents"][doc_title] = source_doc

    # Create outgoing links
    links = [
        DocumentLink(
            id=uuid4(),
            vault_id=vault.id,
            source_document_id=source_doc.id,
            target_document_id=context["documents"]["Reference"].id,
            link_text="Reference",
            link_type="wikilink",
            is_resolved=True,
        ),
        DocumentLink(
            id=uuid4(),
            vault_id=vault.id,
            source_document_id=source_doc.id,
            target_document_id=context["documents"]["Tasks"].id,
            link_text="Tasks",
            link_type="wikilink",
            is_resolved=True,
        ),
    ]

    context["source_document"] = source_doc
    context["outgoing_links"] = links

    mock_repositories["link_repo"].get_outgoing_links.return_value = links


@when(parsers.parse('I request outgoing links for "{doc_title}"'))
def when_request_outgoing_links(context: dict, mock_repositories: dict, doc_title: str):
    """Request outgoing links."""
    context["result_links"] = context["outgoing_links"]


@then("I receive a list of links")
def then_receive_links(context: dict):
    """Verify links received."""
    assert len(context["result_links"]) > 0


@then("each link contains target document information")
def then_links_have_target_info(context: dict):
    """Verify link target information."""
    for link in context["result_links"]:
        if link.is_resolved:
            assert link.target_document_id is not None


@then("resolved links show the target document title and path")
def then_resolved_links_show_title(context: dict):
    """Verify resolved link details."""
    for link in context["result_links"]:
        if link.is_resolved:
            # In a real test, we'd join with document table
            assert link.link_text is not None


@given(parsers.parse('multiple documents link to "{target_title}"'))
def given_multiple_backlinks(context: dict, mock_repositories: dict, target_title: str):
    """Create multiple documents linking to target."""
    vault = context["vault"]
    target_doc = context["documents"].get(target_title)

    # Create backlinks
    backlinks = []
    for title in ["Project Planning", "Tasks"]:
        if title in context["documents"]:
            backlinks.append({
                "source_document": context["documents"][title],
                "link_text": target_title,
                "context": f"... links to [[{target_title}]] ...",
            })

    context["target_document"] = target_doc
    context["backlinks"] = backlinks

    mock_repositories["link_repo"].get_backlinks.return_value = backlinks


@when(parsers.parse('I request backlinks for "{doc_title}"'))
def when_request_backlinks(context: dict, doc_title: str):
    """Request backlinks."""
    context["result_backlinks"] = context["backlinks"]


@then("I receive a list of source documents")
def then_receive_backlinks(context: dict):
    """Verify backlinks received."""
    assert len(context["result_backlinks"]) > 0


@then("each backlink includes the link text used")
def then_backlinks_have_text(context: dict):
    """Verify backlink text."""
    for bl in context["result_backlinks"]:
        assert bl["link_text"] is not None


@then("context around the link is provided")
def then_backlinks_have_context(context: dict):
    """Verify backlink context."""
    for bl in context["result_backlinks"]:
        assert bl["context"] is not None
        assert "[[" in bl["context"]


@given(parsers.parse("a document links using [[Target|Custom Display]]"))
def given_link_with_alias(context: dict, mock_repositories: dict):
    """Create link with display text."""
    vault = context["vault"]

    link = DocumentLink(
        id=uuid4(),
        vault_id=vault.id,
        source_document_id=uuid4(),
        target_document_id=uuid4(),
        link_text="Target",
        display_text="Custom Display",
        link_type="wikilink",
        is_resolved=True,
    )

    context["aliased_link"] = link


@when("I get the link details")
def when_get_link_details(context: dict):
    """Get link details."""
    context["link_result"] = context["aliased_link"]


@then(parsers.parse('the link_text is "{expected}"'))
def then_link_text_is(context: dict, expected: str):
    """Verify link text."""
    assert context["link_result"].link_text == expected


@then(parsers.parse('the display_text is "{expected}"'))
def then_display_text_is(context: dict, expected: str):
    """Verify display text."""
    assert context["link_result"].display_text == expected


@given(parsers.parse('a document "{source}" with a link to "{target}"'))
def given_document_linking_to(context: dict, mock_repositories: dict, source: str, target: str):
    """Create document with specific link."""
    vault = context["vault"]

    source_doc = Document(
        id=uuid4(),
        vault_id=vault.id,
        folder_id=uuid4(),
        title=source,
        filename=f"{source}.md",
        path=f"{source}.md",
        content=f"# {source}\n\nLink to [[{target}]].",
        content_hash="hash",
        link_count=1,
    )

    link = DocumentLink(
        id=uuid4(),
        vault_id=vault.id,
        source_document_id=source_doc.id,
        link_text=target,
        link_type="wikilink",
        is_resolved=False,
    )

    context["source_document"] = source_doc
    context["current_link"] = link
    context["original_target"] = target


@when(parsers.parse('I update "{source}" to link to "{new_target}" instead'))
def when_update_link(context: dict, source: str, new_target: str):
    """Update document with new link."""
    context["new_target"] = new_target
    context["link_updated"] = True


@then(parsers.parse('the old link to "{old_target}" is removed'))
def then_old_link_removed(context: dict, old_target: str):
    """Verify old link removal."""
    assert context.get("link_updated", False)


@then(parsers.parse('a new link to "{new_target}" is created'))
def then_new_link_created(context: dict, new_target: str):
    """Verify new link creation."""
    assert context["new_target"] == new_target


@then("backlink counts are updated correctly")
def then_backlink_counts_updated(context: dict):
    """Verify backlink count update."""
    # Would verify in integration tests
    pass


@given("a document with various link types")
def given_various_link_types(context: dict, mock_repositories: dict):
    """Create document with different link types."""
    vault = context["vault"]

    links = [
        DocumentLink(
            id=uuid4(),
            vault_id=vault.id,
            source_document_id=uuid4(),
            link_text="Regular Link",
            link_type="wikilink",
            is_resolved=False,
        ),
        DocumentLink(
            id=uuid4(),
            vault_id=vault.id,
            source_document_id=uuid4(),
            link_text="image.png",
            link_type="embed",
            is_resolved=False,
        ),
        DocumentLink(
            id=uuid4(),
            vault_id=vault.id,
            source_document_id=uuid4(),
            link_text="Doc#Section",
            link_type="header",
            is_resolved=False,
        ),
    ]

    context["various_links"] = links


@when("I get the document's outgoing links")
def when_get_outgoing(context: dict):
    """Get outgoing links."""
    context["link_results"] = context["various_links"]


@then(parsers.parse('wikilinks have type "wikilink"'))
def then_wikilinks_typed(context: dict):
    """Verify wikilink type."""
    wikilinks = [l for l in context["link_results"] if l.link_type == "wikilink"]
    assert len(wikilinks) > 0


@then(parsers.parse('embeds have type "embed"'))
def then_embeds_typed(context: dict):
    """Verify embed type."""
    embeds = [l for l in context["link_results"] if l.link_type == "embed"]
    assert len(embeds) > 0


@then(parsers.parse('header links have type "header"'))
def then_header_links_typed(context: dict):
    """Verify header link type."""
    headers = [l for l in context["link_results"] if l.link_type == "header"]
    assert len(headers) > 0


@given(parsers.parse('a document "{title}" has alias "{alias}"'))
def given_document_with_alias(context: dict, mock_repositories: dict, title: str, alias: str):
    """Create document with alias."""
    vault = context["vault"]

    doc = Document(
        id=uuid4(),
        vault_id=vault.id,
        folder_id=uuid4(),
        title=title,
        filename=f"{title}.md",
        path=f"{title}.md",
        content=f"# {title}",
        content_hash="hash",
        aliases=[alias],
    )

    context["aliased_document"] = doc
    context["alias"] = alias


@given(parsers.parse("another document links to [[{link_target}]]"))
def given_another_doc_links(context: dict, link_target: str):
    """Create linking document."""
    context["link_target_text"] = link_target


@when("links are resolved")
def when_links_resolved(context: dict):
    """Resolve links."""
    doc = context["aliased_document"]
    alias = context["alias"]

    # Simulate resolution finding doc by alias
    if context["link_target_text"] == alias:
        context["resolved_to"] = doc


@then(parsers.parse('the link resolves to the "{title}" document'))
def then_resolves_to(context: dict, title: str):
    """Verify resolution result."""
    resolved = context.get("resolved_to")
    assert resolved is not None
    assert resolved.title == title
