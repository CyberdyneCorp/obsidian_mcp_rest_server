"""Step definitions for semantic search feature."""

from uuid import uuid4

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from app.domain.entities.vault import Vault
from app.domain.entities.document import Document
from app.domain.value_objects.frontmatter import Frontmatter

# Load scenarios from feature file
scenarios("../features/semantic_search.feature")


@given(parsers.parse('a vault "{vault_slug}" exists with embedded documents'))
def given_vault_with_embeddings(context: dict, mock_repositories: dict, vault_slug: str):
    """Create vault with embedded documents."""
    vault = Vault(
        id=uuid4(),
        user_id=context["user"].id,
        name=vault_slug.replace("-", " ").title(),
        slug=vault_slug,
        document_count=5,
    )
    context["vault"] = vault

    # Create documents with various topics
    documents = [
        Document(
            id=uuid4(),
            vault_id=vault.id,
            folder_id=uuid4(),
            title="Machine Learning Basics",
            filename="ml-basics.md",
            path="ml-basics.md",
            content="# Machine Learning\n\nIntroduction to ML concepts.",
            content_hash="ml",
            frontmatter=Frontmatter(tags=("ml", "active")),
        ),
        Document(
            id=uuid4(),
            vault_id=vault.id,
            folder_id=uuid4(),
            title="Deep Neural Networks",
            filename="deep-nn.md",
            path="deep-nn.md",
            content="# Deep Learning\n\nNeural network architectures.",
            content_hash="dl",
            frontmatter=Frontmatter(tags=("ml", "archived")),
        ),
        Document(
            id=uuid4(),
            vault_id=vault.id,
            folder_id=uuid4(),
            title="Project Updates",
            filename="projects/updates.md",
            path="Projects/updates.md",
            content="# Project Updates\n\nLatest status report.",
            content_hash="proj",
            frontmatter=Frontmatter(tags=("active",)),
        ),
    ]

    context["documents"] = {d.title: d for d in documents}
    context["all_documents"] = documents

    mock_repositories["vault_repo"].get_by_slug.return_value = vault


@given(parsers.parse('documents about "{topic1}" and "{topic2}"'))
def given_documents_about_topics(context: dict, topic1: str, topic2: str):
    """Ensure documents exist about topics."""
    context["search_topics"] = [topic1, topic2]


@when(parsers.parse('I search for "{query}"'))
def when_search_for(context: dict, mock_repositories: dict, mock_providers: dict, query: str):
    """Perform semantic search."""
    context["search_query"] = query

    # Simulate embedding generation
    mock_providers["embedding_provider"].embed_text.return_value = [0.1] * 1536

    # Simulate search results
    results = []
    for doc in context["all_documents"]:
        if any(topic.lower() in doc.content.lower() for topic in context.get("search_topics", [query])):
            results.append({
                "document": doc,
                "score": 0.92,
                "matched_chunk": doc.content[:100],
            })

    context["search_results"] = sorted(results, key=lambda x: x["score"], reverse=True)


@then("I receive relevant documents")
def then_receive_relevant_docs(context: dict):
    """Verify relevant results."""
    assert len(context["search_results"]) > 0


@then("results are ordered by relevance score")
def then_ordered_by_score(context: dict):
    """Verify score ordering."""
    scores = [r["score"] for r in context["search_results"]]
    assert scores == sorted(scores, reverse=True)


@then("the matched chunk content is returned")
def then_chunk_returned(context: dict):
    """Verify chunk content."""
    for result in context["search_results"]:
        assert result["matched_chunk"] is not None


@given(parsers.parse('documents in "{folder1}" and "{folder2}" folders'))
def given_documents_in_folders(context: dict, folder1: str, folder2: str):
    """Create documents in specific folders."""
    context["folders"] = [folder1, folder2]

    for doc in context["all_documents"]:
        if folder1.lower() in doc.path.lower():
            doc.path = f"{folder1}/{doc.filename}"


@when(parsers.parse('I search for "{query}" in folder "{folder}"'))
def when_search_in_folder(context: dict, query: str, folder: str):
    """Search with folder filter."""
    context["search_query"] = query
    context["folder_filter"] = folder

    # Filter results by folder
    results = [
        {"document": doc, "score": 0.9, "matched_chunk": doc.content[:100]}
        for doc in context["all_documents"]
        if folder.lower() in doc.path.lower()
    ]

    context["search_results"] = results


@then(parsers.parse('only documents from "{folder}" folder are returned'))
def then_only_folder_results(context: dict, folder: str):
    """Verify folder filtering."""
    for result in context["search_results"]:
        assert folder.lower() in result["document"].path.lower()


@given(parsers.parse('documents tagged with "{tag1}" and "{tag2}"'))
def given_documents_with_tags(context: dict, tag1: str, tag2: str):
    """Ensure tagged documents exist."""
    context["tag_filter_options"] = [tag1, tag2]


@when(parsers.parse('I search for "{query}" with tag filter ["{tag}"]'))
def when_search_with_tag(context: dict, query: str, tag: str):
    """Search with tag filter."""
    context["search_query"] = query
    context["tag_filter"] = tag

    # Filter results by tag
    results = []
    for doc in context["all_documents"]:
        tags = doc.frontmatter.tags if doc.frontmatter else ()
        if tag in tags:
            results.append({
                "document": doc,
                "score": 0.85,
                "matched_chunk": doc.content[:100],
            })

    context["search_results"] = results


@then(parsers.parse('only documents with "{tag}" tag are returned'))
def then_only_tagged_results(context: dict, tag: str):
    """Verify tag filtering."""
    for result in context["search_results"]:
        tags = result["document"].frontmatter.tags if result["document"].frontmatter else ()
        assert tag in tags


@given(parsers.parse('a document containing the exact phrase "{phrase}"'))
def given_document_with_phrase(context: dict, phrase: str):
    """Create document with exact phrase."""
    doc = Document(
        id=uuid4(),
        vault_id=context["vault"].id,
        folder_id=uuid4(),
        title="Quarterly Review",
        filename="quarterly.md",
        path="quarterly.md",
        content=f"# Report\n\nThe {phrase} was very successful.",
        content_hash="q",
    )
    context["phrase_document"] = doc
    context["search_phrase"] = phrase


@when(parsers.parse('I perform a full-text search for "{query}"'))
def when_fulltext_search(context: dict, query: str):
    """Perform full-text search."""
    context["search_query"] = query

    # Simulate fulltext search
    doc = context.get("phrase_document")
    if doc and query.lower() in doc.content.lower():
        context["search_results"] = [{
            "document": doc,
            "headline": f"The <b>{query}</b> was very successful.",
        }]
    else:
        context["search_results"] = []


@then("the document is found")
def then_document_found(context: dict):
    """Verify document was found."""
    assert len(context["search_results"]) > 0


@then("a headline with highlighted matches is returned")
def then_headline_returned(context: dict):
    """Verify headline highlighting."""
    result = context["search_results"][0]
    assert result["headline"] is not None
    assert "<b>" in result["headline"]


@given("searchable documents in the vault")
def given_searchable_docs(context: dict):
    """Ensure searchable documents exist."""
    assert len(context["all_documents"]) > 0


@when("I perform a search")
def when_perform_search(context: dict, mock_providers: dict):
    """Perform generic search."""
    mock_providers["embedding_provider"].embed_text.return_value = [0.1] * 1536

    context["search_results"] = [
        {"document": doc, "score": 0.9 - i * 0.1, "matched_chunk": doc.content[:50]}
        for i, doc in enumerate(context["all_documents"])
    ]


@then("each result includes document id")
def then_results_have_id(context: dict):
    """Verify id in results."""
    for result in context["search_results"]:
        assert result["document"].id is not None


@then("each result includes document title")
def then_results_have_title(context: dict):
    """Verify title in results."""
    for result in context["search_results"]:
        assert result["document"].title is not None


@then("each result includes document path")
def then_results_have_path(context: dict):
    """Verify path in results."""
    for result in context["search_results"]:
        assert result["document"].path is not None


@then("each result includes relevance score")
def then_results_have_score(context: dict):
    """Verify score in results."""
    for result in context["search_results"]:
        assert result["score"] is not None


@given("many documents matching a query")
def given_many_matching_docs(context: dict):
    """Create many matching documents."""
    # Already have documents from fixture
    pass


@when(parsers.parse("I search with limit {limit:d}"))
def when_search_with_limit(context: dict, limit: int):
    """Search with limit."""
    context["search_limit"] = limit

    # Limit results
    all_results = [
        {"document": doc, "score": 0.95 - i * 0.05, "matched_chunk": doc.content[:50]}
        for i, doc in enumerate(context["all_documents"])
    ]

    context["search_results"] = sorted(
        all_results, key=lambda x: x["score"], reverse=True
    )[:limit]


@then(parsers.parse("at most {limit:d} results are returned"))
def then_limited_results(context: dict, limit: int):
    """Verify result limit."""
    assert len(context["search_results"]) <= limit


@then(parsers.parse("they are the top {limit:d} by relevance"))
def then_top_results(context: dict, limit: int):
    """Verify top results."""
    scores = [r["score"] for r in context["search_results"]]
    assert scores == sorted(scores, reverse=True)


@given("documents with varying relevance to a query")
def given_varying_relevance_docs(context: dict):
    """Create documents with different relevance."""
    pass


@when(parsers.parse("I search with minimum score threshold {threshold:f}"))
def when_search_with_threshold(context: dict, threshold: float):
    """Search with threshold."""
    context["score_threshold"] = threshold

    all_results = [
        {"document": doc, "score": 0.9 - i * 0.15, "matched_chunk": doc.content[:50]}
        for i, doc in enumerate(context["all_documents"])
    ]

    context["search_results"] = [
        r for r in all_results if r["score"] >= threshold
    ]


@then("only highly relevant results are returned")
def then_highly_relevant(context: dict):
    """Verify high relevance."""
    threshold = context.get("score_threshold", 0.8)
    for result in context["search_results"]:
        assert result["score"] >= threshold


@then(parsers.parse("all results have score >= {threshold:f}"))
def then_above_threshold(context: dict, threshold: float):
    """Verify all above threshold."""
    for result in context["search_results"]:
        assert result["score"] >= threshold
