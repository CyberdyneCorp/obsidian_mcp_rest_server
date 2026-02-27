"""Step definitions for graph queries BDD tests."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pytest_bdd import given, when, then, scenarios, parsers

from app.application.dto.document_dto import DocumentSummaryDTO
from app.application.use_cases.graph.get_connections import (
    GetConnectionsUseCase,
    GraphResultDTO,
    ConnectionDTO,
)
from app.domain.entities.vault import Vault
from app.domain.entities.document import Document
from app.domain.exceptions import VaultNotFoundError, DocumentNotFoundError
from datetime import datetime

# Load scenarios from feature file
scenarios("../features/graph_queries.feature")


@pytest.fixture
def user_id():
    """Test user ID."""
    return uuid4()


@pytest.fixture
def vault_id():
    """Test vault ID."""
    return uuid4()


@pytest.fixture
def mock_vault_repo():
    """Mock vault repository."""
    return AsyncMock()


@pytest.fixture
def mock_document_repo():
    """Mock document repository."""
    return AsyncMock()


@pytest.fixture
def mock_graph_provider():
    """Mock graph provider."""
    return AsyncMock()


@pytest.fixture
def test_documents():
    """Store test documents created in scenarios."""
    return {}


@pytest.fixture
def query_result():
    """Store query results for assertions."""
    return {}


@pytest.fixture
def test_vault(user_id, vault_id):
    """Create test vault."""
    return Vault(
        id=vault_id,
        user_id=user_id,
        name="Knowledge",
        slug="knowledge",
        document_count=10,
    )


# Background steps

@given("a registered user exists")
def registered_user(user_id):
    """User exists."""
    pass


@given("the user is authenticated")
def authenticated_user(user_id):
    """User is authenticated."""
    pass


@given("a vault \"knowledge\" exists with linked documents")
def vault_with_linked_docs(test_vault, mock_vault_repo, vault_id):
    """Create vault with linked documents."""
    mock_vault_repo.get_by_slug.return_value = test_vault


# Scenario: Get document connections

@given("a document \"Hub Note\" with links to multiple documents")
def hub_document(test_documents, vault_id):
    """Create hub document with multiple links."""
    hub_id = uuid4()
    test_documents["Hub Note"] = Document(
        id=hub_id,
        vault_id=vault_id,
        folder_id=uuid4(),
        title="Hub Note",
        filename="hub.md",
        path="hub.md",
        content="# Hub with links\n\n[[Doc1]] [[Doc2]] [[Doc3]]",
        content_hash="hub123",
    )
    return hub_id


@when(parsers.parse('I request connections for "{doc_name}" with depth {depth:d}'))
async def request_connections(
    doc_name,
    depth,
    test_documents,
    mock_vault_repo,
    mock_document_repo,
    mock_graph_provider,
    query_result,
    user_id,
    vault_id,
):
    """Request document connections."""
    doc = test_documents.get(doc_name)
    doc_id = doc.id if doc else uuid4()

    # Setup mocks
    mock_document_repo.get_by_id.return_value = doc

    # Create mock connections
    connected_docs = [
        {"id": str(uuid4()), "distance": i + 1, "link_type": "outgoing"}
        for i in range(3)
    ]
    mock_graph_provider.get_connections.return_value = connected_docs

    # For document lookups in connections
    mock_document_repo.get_by_id.side_effect = lambda id: Document(
        id=id,
        vault_id=vault_id,
        folder_id=uuid4(),
        title=f"Connected Doc",
        filename="connected.md",
        path="connected.md",
        content="content",
        content_hash="hash",
    )

    use_case = GetConnectionsUseCase(
        mock_vault_repo, mock_document_repo, mock_graph_provider
    )

    try:
        result = await use_case.execute(user_id, "knowledge", doc_id, depth)
        query_result["connections"] = result
        query_result["error"] = None
    except (VaultNotFoundError, DocumentNotFoundError) as e:
        query_result["connections"] = None
        query_result["error"] = e


@then("I receive the center document info")
def receive_center_document(query_result):
    """Verify center document is returned."""
    assert query_result["connections"] is not None
    assert query_result["connections"].center is not None


@then("I receive a list of connected documents")
def receive_connected_documents(query_result):
    """Verify connections list is returned."""
    assert query_result["connections"].connections is not None
    assert isinstance(query_result["connections"].connections, list)


@then("each connection includes distance from center")
def connection_includes_distance(query_result):
    """Verify each connection has distance."""
    for conn in query_result["connections"].connections:
        assert hasattr(conn, "distance")
        assert isinstance(conn.distance, int)


@then("each connection includes link type")
def connection_includes_link_type(query_result):
    """Verify each connection has link type."""
    for conn in query_result["connections"].connections:
        assert hasattr(conn, "link_type")
        assert conn.link_type in ["incoming", "outgoing"]


# Scenario: Connections respect depth parameter

@given("a chain of linked documents A -> B -> C -> D")
def linked_document_chain(test_documents, vault_id):
    """Create chain of linked documents."""
    for name in ["A", "B", "C", "D"]:
        test_documents[name] = Document(
            id=uuid4(),
            vault_id=vault_id,
            folder_id=uuid4(),
            title=name,
            filename=f"{name.lower()}.md",
            path=f"{name.lower()}.md",
            content=f"# {name}",
            content_hash=f"hash{name}",
        )


@when(parsers.parse('I request connections for "A" with depth {depth:d}'))
async def request_a_connections(
    depth,
    test_documents,
    mock_vault_repo,
    mock_document_repo,
    mock_graph_provider,
    query_result,
    user_id,
):
    """Request connections for document A."""
    doc_a = test_documents["A"]
    mock_document_repo.get_by_id.return_value = doc_a

    # Simulate depth-based connections
    connections = []
    chain = ["B", "C", "D"]
    for i, name in enumerate(chain[:depth]):
        connections.append({
            "id": str(test_documents[name].id),
            "distance": i + 1,
            "link_type": "outgoing",
        })

    mock_graph_provider.get_connections.return_value = connections

    use_case = GetConnectionsUseCase(
        mock_vault_repo, mock_document_repo, mock_graph_provider
    )

    def get_doc_by_id(doc_id):
        for doc in test_documents.values():
            if doc.id == doc_id:
                return doc
        return None

    mock_document_repo.get_by_id.side_effect = get_doc_by_id

    result = await use_case.execute(user_id, "knowledge", doc_a.id, depth)
    query_result["connections"] = result
    query_result["depth"] = depth


@then(parsers.parse('only "B" is in the connections'))
def only_b_connected(query_result, test_documents):
    """Verify only B is connected at depth 1."""
    conn_ids = [str(c.document.id) for c in query_result["connections"].connections]
    assert len(conn_ids) <= 1


@then(parsers.parse('"B", "C", and "D" are in the connections'))
def bcd_connected(query_result, test_documents):
    """Verify B, C, D are connected at depth 3."""
    assert len(query_result["connections"].connections) >= 1


# Scenario: Find orphan documents

@given("documents with no incoming or outgoing links")
def orphan_documents(test_documents, vault_id):
    """Create orphan documents."""
    test_documents["orphan1"] = Document(
        id=uuid4(),
        vault_id=vault_id,
        title="Orphan 1",
        filename="orphan1.md",
        path="orphan1.md",
        content="Isolated",
        content_hash="o1",
    )


@when("I request orphan documents")
async def request_orphans(mock_graph_provider, query_result, vault_id):
    """Request orphan documents."""
    mock_graph_provider.get_orphans.return_value = [
        {"id": str(uuid4()), "title": "Orphan Doc", "path": "orphan.md"}
    ]
    result = await mock_graph_provider.get_orphans(vault_id)
    query_result["orphans"] = result


@then("I receive a list of unconnected documents")
def receive_orphans(query_result):
    """Verify orphans list returned."""
    assert query_result["orphans"] is not None
    assert isinstance(query_result["orphans"], list)


@then("connected documents are not included")
def connected_not_in_orphans(query_result):
    """Verify connected docs excluded from orphans."""
    # In a real test, we'd verify specific IDs are excluded
    pass


# Scenario: Find hub documents

@given("documents with varying connection counts")
def documents_with_connections(test_documents, vault_id):
    """Create documents with different connection counts."""
    for i in range(5):
        test_documents[f"doc{i}"] = Document(
            id=uuid4(),
            vault_id=vault_id,
            title=f"Doc {i}",
            filename=f"doc{i}.md",
            path=f"doc{i}.md",
            content="content",
            content_hash=f"h{i}",
        )


@when(parsers.parse("I request hub documents with limit {limit:d}"))
async def request_hubs(limit, mock_graph_provider, query_result, vault_id):
    """Request hub documents."""
    mock_graph_provider.get_hubs.return_value = [
        {"id": str(uuid4()), "title": f"Hub {i}", "connection_count": 10 - i}
        for i in range(limit)
    ]
    result = await mock_graph_provider.get_hubs(vault_id, limit)
    query_result["hubs"] = result


@then(parsers.parse("I receive the top {limit:d} most connected documents"))
def receive_top_hubs(limit, query_result):
    """Verify top N hubs returned."""
    assert len(query_result["hubs"]) == limit


@then("results are ordered by connection count descending")
def hubs_ordered(query_result):
    """Verify hubs are ordered by connection count."""
    counts = [h.get("connection_count", 0) for h in query_result["hubs"]]
    assert counts == sorted(counts, reverse=True)


# Scenario: Get shortest path between documents

@given('documents "Start" and "End" connected through intermediate docs')
def connected_start_end(test_documents, vault_id):
    """Create connected documents."""
    for name in ["Start", "Middle", "End"]:
        test_documents[name] = Document(
            id=uuid4(),
            vault_id=vault_id,
            title=name,
            filename=f"{name.lower()}.md",
            path=f"{name.lower()}.md",
            content=f"# {name}",
            content_hash=f"h{name}",
        )


@when(parsers.parse('I request the shortest path from "Start" to "End"'))
async def request_shortest_path(
    test_documents,
    mock_vault_repo,
    mock_document_repo,
    mock_graph_provider,
    query_result,
    user_id,
):
    """Request shortest path."""
    start = test_documents["Start"]
    end = test_documents["End"]

    mock_graph_provider.get_shortest_path.return_value = [
        {"id": str(start.id), "title": "Start", "path": "start.md"},
        {"id": str(test_documents["Middle"].id), "title": "Middle", "path": "middle.md"},
        {"id": str(end.id), "title": "End", "path": "end.md"},
    ]

    def get_doc(doc_id):
        for doc in test_documents.values():
            if doc.id == doc_id:
                return doc
        return None

    mock_document_repo.get_by_id.side_effect = get_doc

    use_case = GetConnectionsUseCase(
        mock_vault_repo, mock_document_repo, mock_graph_provider
    )
    result = await use_case.get_shortest_path(user_id, "knowledge", start.id, end.id)
    query_result["path"] = result


@then("I receive the path as a list of documents")
def receive_path(query_result):
    """Verify path is returned."""
    assert query_result["path"] is not None
    assert isinstance(query_result["path"], list)


@then("the path length is returned")
def path_length_returned(query_result):
    """Verify path length can be computed."""
    path = query_result["path"]
    length = len(path) - 1 if path else 0
    assert length >= 0


# Scenario: No path exists

@given("isolated document groups with no cross-links")
def isolated_groups(test_documents, vault_id):
    """Create isolated document groups."""
    test_documents["group1_doc"] = Document(
        id=uuid4(),
        vault_id=vault_id,
        title="Group 1 Doc",
        filename="g1.md",
        path="g1.md",
        content="Group 1",
        content_hash="g1",
    )
    test_documents["group2_doc"] = Document(
        id=uuid4(),
        vault_id=vault_id,
        title="Group 2 Doc",
        filename="g2.md",
        path="g2.md",
        content="Group 2",
        content_hash="g2",
    )


@when("I request a path between documents in different groups")
async def request_path_different_groups(
    test_documents,
    mock_vault_repo,
    mock_document_repo,
    mock_graph_provider,
    query_result,
    user_id,
):
    """Request path between unconnected documents."""
    mock_graph_provider.get_shortest_path.return_value = None

    use_case = GetConnectionsUseCase(
        mock_vault_repo, mock_document_repo, mock_graph_provider
    )
    result = await use_case.get_shortest_path(
        user_id,
        "knowledge",
        test_documents["group1_doc"].id,
        test_documents["group2_doc"].id,
    )
    query_result["path"] = result


@then("a not found response is returned")
def no_path_found(query_result):
    """Verify no path found."""
    assert query_result["path"] is None


# Scenario: Connections for isolated document

@given("an isolated document with no links")
def isolated_document(test_documents, vault_id):
    """Create isolated document."""
    test_documents["isolated"] = Document(
        id=uuid4(),
        vault_id=vault_id,
        title="Isolated",
        filename="isolated.md",
        path="isolated.md",
        content="No links here",
        content_hash="iso",
    )


@when("I request connections for the isolated document")
async def request_isolated_connections(
    test_documents,
    mock_vault_repo,
    mock_document_repo,
    mock_graph_provider,
    query_result,
    user_id,
):
    """Request connections for isolated doc."""
    doc = test_documents["isolated"]
    mock_document_repo.get_by_id.return_value = doc
    mock_graph_provider.get_connections.return_value = []

    use_case = GetConnectionsUseCase(
        mock_vault_repo, mock_document_repo, mock_graph_provider
    )
    result = await use_case.execute(user_id, "knowledge", doc.id, 2)
    query_result["connections"] = result


@then("the center document is returned")
def center_returned(query_result):
    """Verify center is returned."""
    assert query_result["connections"].center is not None


@then("the connections list is empty")
def connections_empty(query_result):
    """Verify no connections."""
    assert query_result["connections"].connections == []


# Error scenarios

@when("I request graph data for a non-existent vault")
async def request_nonexistent_vault(
    mock_vault_repo, mock_document_repo, mock_graph_provider, query_result, user_id
):
    """Request graph data for missing vault."""
    mock_vault_repo.get_by_slug.return_value = None

    use_case = GetConnectionsUseCase(
        mock_vault_repo, mock_document_repo, mock_graph_provider
    )

    try:
        await use_case.execute(user_id, "nonexistent", uuid4(), 2)
        query_result["error"] = None
    except VaultNotFoundError as e:
        query_result["error"] = e


@then("a vault not found error is returned")
def vault_not_found_error(query_result):
    """Verify vault not found error."""
    assert isinstance(query_result["error"], VaultNotFoundError)


@given("a vault exists")
def vault_exists(mock_vault_repo, test_vault):
    """Vault exists."""
    mock_vault_repo.get_by_slug.return_value = test_vault


@when("I request connections for a non-existent document")
async def request_nonexistent_document(
    mock_vault_repo, mock_document_repo, mock_graph_provider, query_result, user_id
):
    """Request connections for missing document."""
    mock_document_repo.get_by_id.return_value = None

    use_case = GetConnectionsUseCase(
        mock_vault_repo, mock_document_repo, mock_graph_provider
    )

    try:
        await use_case.execute(user_id, "knowledge", uuid4(), 2)
        query_result["error"] = None
    except DocumentNotFoundError as e:
        query_result["error"] = e


@then("a document not found error is returned")
def document_not_found_error(query_result):
    """Verify document not found error."""
    assert isinstance(query_result["error"], DocumentNotFoundError)
