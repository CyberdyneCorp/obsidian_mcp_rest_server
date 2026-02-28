"""Tests for MCP tools."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.dto.document_dto import DocumentDTO, DocumentSummaryDTO
from app.application.dto.search_dto import SearchResultDTO, FulltextSearchResultDTO
from app.application.dto.link_dto import BacklinkDTO, BacklinkSourceDTO
from app.application.dto.table_dto import TableSummaryDTO, TableDTO, ColumnDTO, RowDTO
from app.application.use_cases.graph.get_connections import GraphResultDTO, ConnectionDTO
from app.domain.entities.vault import Vault
from app.domain.entities.document import Document
from app.infrastructure.mcp.tools import register_mcp_tools


class MockMCP:
    """Mock FastMCP server for testing tool registration."""

    def __init__(self):
        self.tools = {}

    def tool(self):
        """Decorator to register a tool."""
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator


@pytest.fixture
def mock_mcp():
    """Create mock MCP instance."""
    return MockMCP()


@pytest.fixture
def user_id():
    """Create test user ID."""
    return uuid4()


@pytest.fixture
def vault_id():
    """Create test vault ID."""
    return uuid4()


@pytest.fixture
def mock_dependencies(user_id, vault_id):
    """Create mock dependencies for MCP tools."""
    # Mock use cases
    list_vaults_use_case = AsyncMock()
    get_document_use_case = AsyncMock()
    semantic_search_use_case = AsyncMock()
    fulltext_search_use_case = AsyncMock()
    get_backlinks_use_case = AsyncMock()
    get_connections_use_case = AsyncMock()
    list_documents_use_case = AsyncMock()
    # Table/row use cases
    list_tables_use_case = AsyncMock()
    get_table_use_case = AsyncMock()
    list_rows_use_case = AsyncMock()
    get_row_use_case = AsyncMock()
    execute_query_use_case = AsyncMock()

    return {
        "current_user_id": user_id,
        "list_vaults_use_case": list_vaults_use_case,
        "get_document_use_case": get_document_use_case,
        "semantic_search_use_case": semantic_search_use_case,
        "fulltext_search_use_case": fulltext_search_use_case,
        "get_backlinks_use_case": get_backlinks_use_case,
        "get_connections_use_case": get_connections_use_case,
        "list_documents_use_case": list_documents_use_case,
        # Table/row use cases
        "list_tables_use_case": list_tables_use_case,
        "get_table_use_case": get_table_use_case,
        "list_rows_use_case": list_rows_use_case,
        "get_row_use_case": get_row_use_case,
        "execute_query_use_case": execute_query_use_case,
    }


class TestMCPToolsRegistration:
    """Tests for MCP tools registration."""

    def test_all_tools_registered(self, mock_mcp, mock_dependencies):
        """Test that all MCP tools are registered."""
        register_mcp_tools(mock_mcp, mock_dependencies)

        expected_tools = [
            "list_vaults",
            "get_document",
            "search_documents",
            "get_backlinks",
            "get_connections",
            "list_documents",
            # Structured data tools
            "list_tables",
            "get_table",
            "list_table_rows",
            "get_table_row",
            "query_table",
        ]

        for tool_name in expected_tools:
            assert tool_name in mock_mcp.tools, f"Tool {tool_name} not registered"


@pytest.mark.asyncio
class TestListVaultsTool:
    """Tests for list_vaults MCP tool."""

    async def test_list_vaults_returns_vault_list(
        self, mock_mcp, mock_dependencies, user_id, vault_id
    ):
        """Test listing vaults returns formatted list."""
        mock_dependencies["list_vaults_use_case"].execute.return_value = [
            Vault(
                id=vault_id,
                user_id=user_id,
                name="My Vault",
                slug="my-vault",
                document_count=10,
            ),
            Vault(
                id=uuid4(),
                user_id=user_id,
                name="Second Vault",
                slug="second-vault",
                document_count=5,
            ),
        ]

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["list_vaults"]()

        assert len(result) == 2
        assert result[0]["name"] == "My Vault"
        assert result[0]["slug"] == "my-vault"
        assert result[0]["document_count"] == 10
        assert result[0]["id"] == str(vault_id)

    async def test_list_vaults_empty(self, mock_mcp, mock_dependencies):
        """Test listing vaults when user has none."""
        mock_dependencies["list_vaults_use_case"].execute.return_value = []

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["list_vaults"]()

        assert result == []


@pytest.mark.asyncio
class TestGetDocumentTool:
    """Tests for get_document MCP tool."""

    async def test_get_document_by_id(self, mock_mcp, mock_dependencies, vault_id):
        """Test getting document by ID."""
        doc_id = uuid4()
        mock_dependencies["get_document_use_case"].execute.return_value = DocumentDTO(
            id=doc_id,
            title="Test Document",
            path="Notes/test.md",
            content="# Test content",
            frontmatter={"tags": ["test"]},
            tags=["test"],
            aliases=[],
            word_count=100,
            link_count=2,
            backlink_count=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["get_document"](
            vault_slug="my-vault",
            document_id=str(doc_id),
        )

        assert result["id"] == str(doc_id)
        assert result["title"] == "Test Document"
        assert result["path"] == "Notes/test.md"
        assert result["content"] == "# Test content"
        assert result["word_count"] == 100

    async def test_get_document_by_path(self, mock_mcp, mock_dependencies, vault_id):
        """Test getting document by path."""
        doc_id = uuid4()
        mock_dependencies["get_document_use_case"].execute.return_value = DocumentDTO(
            id=doc_id,
            title="My Note",
            path="Projects/my-note.md",
            content="# My Note\n\nContent here.",
            frontmatter={},
            tags=[],
            aliases=[],
            word_count=5,
            link_count=0,
            backlink_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["get_document"](
            vault_slug="my-vault",
            path="Projects/my-note.md",
        )

        assert result["path"] == "Projects/my-note.md"
        assert result["title"] == "My Note"


@pytest.mark.asyncio
class TestSearchDocumentsTool:
    """Tests for search_documents MCP tool."""

    async def test_semantic_search(self, mock_mcp, mock_dependencies, vault_id):
        """Test semantic search returns formatted results."""
        doc_id = uuid4()
        mock_dependencies["semantic_search_use_case"].execute.return_value = [
            SearchResultDTO(
                document=DocumentSummaryDTO(
                    id=doc_id,
                    title="Relevant Document",
                    path="docs/relevant.md",
                    word_count=200,
                    link_count=3,
                    backlink_count=2,
                    tags=["ai", "ml"],
                    updated_at=datetime.now(),
                ),
                score=0.92,
                matched_chunk="This is the relevant chunk about AI.",
            ),
        ]

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["search_documents"](
            vault_slug="my-vault",
            query="artificial intelligence",
            search_type="semantic",
            limit=10,
        )

        assert len(result) == 1
        assert result[0]["id"] == str(doc_id)
        assert result[0]["title"] == "Relevant Document"
        assert result[0]["score"] == 0.92
        assert "matched_chunk" in result[0]

    async def test_fulltext_search(self, mock_mcp, mock_dependencies, vault_id):
        """Test fulltext search returns formatted results."""
        doc_id = uuid4()
        mock_dependencies["fulltext_search_use_case"].execute.return_value = [
            FulltextSearchResultDTO(
                document=DocumentSummaryDTO(
                    id=doc_id,
                    title="Exact Match",
                    path="notes/exact.md",
                    word_count=150,
                    link_count=1,
                    backlink_count=0,
                    tags=[],
                    updated_at=datetime.now(),
                ),
                headline="...this is the <b>exact match</b> in context...",
            ),
        ]

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["search_documents"](
            vault_slug="my-vault",
            query="exact match",
            search_type="fulltext",
            limit=5,
        )

        assert len(result) == 1
        assert result[0]["title"] == "Exact Match"
        assert "headline" in result[0]
        assert "exact match" in result[0]["headline"]

    async def test_search_with_filters(self, mock_mcp, mock_dependencies, vault_id):
        """Test search with folder and tag filters."""
        mock_dependencies["semantic_search_use_case"].execute.return_value = []

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["search_documents"](
            vault_slug="my-vault",
            query="test query",
            search_type="semantic",
            limit=10,
            folder="Projects",
            tags=["important", "active"],
        )

        # Verify use case was called with correct filters
        call_args = mock_dependencies["semantic_search_use_case"].execute.call_args
        search_dto = call_args[0][2]  # Third positional arg
        assert search_dto.folder == "Projects"
        assert search_dto.tags == ["important", "active"]

    async def test_search_empty_results(self, mock_mcp, mock_dependencies):
        """Test search with no results."""
        mock_dependencies["semantic_search_use_case"].execute.return_value = []

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["search_documents"](
            vault_slug="my-vault",
            query="nonexistent term",
            search_type="semantic",
        )

        assert result == []


@pytest.mark.asyncio
class TestGetBacklinksTool:
    """Tests for get_backlinks MCP tool."""

    async def test_get_backlinks_returns_list(self, mock_mcp, mock_dependencies, vault_id):
        """Test getting backlinks returns formatted list."""
        target_id = uuid4()
        source_id = uuid4()

        mock_dependencies["get_backlinks_use_case"].execute.return_value = [
            BacklinkDTO(
                document=BacklinkSourceDTO(
                    id=source_id,
                    title="Linking Document",
                    path="notes/linker.md",
                ),
                link_text="Target Document",
                context="See [[Target Document]] for more info.",
            ),
        ]

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["get_backlinks"](
            vault_slug="my-vault",
            document_id=str(target_id),
        )

        assert len(result) == 1
        assert result[0]["document"]["id"] == str(source_id)
        assert result[0]["document"]["title"] == "Linking Document"
        assert result[0]["link_text"] == "Target Document"
        assert "context" in result[0]

    async def test_get_backlinks_empty(self, mock_mcp, mock_dependencies):
        """Test getting backlinks when none exist."""
        mock_dependencies["get_backlinks_use_case"].execute.return_value = []

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["get_backlinks"](
            vault_slug="my-vault",
            document_id=str(uuid4()),
        )

        assert result == []


@pytest.mark.asyncio
class TestGetConnectionsTool:
    """Tests for get_connections MCP tool."""

    async def test_get_connections_returns_graph(
        self, mock_mcp, mock_dependencies, vault_id
    ):
        """Test getting connections returns graph structure."""
        center_id = uuid4()
        connected_id = uuid4()

        mock_dependencies["get_connections_use_case"].execute.return_value = GraphResultDTO(
            center=DocumentSummaryDTO(
                id=center_id,
                title="Center Document",
                path="center.md",
                word_count=100,
                link_count=3,
                backlink_count=2,
                tags=[],
                updated_at=datetime.now(),
            ),
            connections=[
                ConnectionDTO(
                    document=DocumentSummaryDTO(
                        id=connected_id,
                        title="Connected Doc",
                        path="connected.md",
                        word_count=50,
                        link_count=1,
                        backlink_count=1,
                        tags=["related"],
                        updated_at=datetime.now(),
                    ),
                    distance=1,
                    link_type="outgoing",
                ),
            ],
        )

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["get_connections"](
            vault_slug="my-vault",
            document_id=str(center_id),
            depth=2,
        )

        assert "center" in result
        assert result["center"]["id"] == str(center_id)
        assert result["center"]["title"] == "Center Document"

        assert "connections" in result
        assert len(result["connections"]) == 1
        assert result["connections"][0]["id"] == str(connected_id)
        assert result["connections"][0]["distance"] == 1
        assert result["connections"][0]["link_type"] == "outgoing"

    async def test_get_connections_with_depth(self, mock_mcp, mock_dependencies, vault_id):
        """Test connections with custom depth parameter."""
        center_id = uuid4()

        mock_dependencies["get_connections_use_case"].execute.return_value = GraphResultDTO(
            center=DocumentSummaryDTO(
                id=center_id,
                title="Hub",
                path="hub.md",
                word_count=100,
                link_count=10,
                backlink_count=5,
                tags=[],
                updated_at=datetime.now(),
            ),
            connections=[],
        )

        register_mcp_tools(mock_mcp, mock_dependencies)
        await mock_mcp.tools["get_connections"](
            vault_slug="my-vault",
            document_id=str(center_id),
            depth=5,
        )

        # Verify depth was passed to use case
        call_args = mock_dependencies["get_connections_use_case"].execute.call_args
        assert call_args[0][3] == 5  # Fourth positional arg is depth

    async def test_get_connections_no_connections(
        self, mock_mcp, mock_dependencies, vault_id
    ):
        """Test getting connections for isolated document."""
        isolated_id = uuid4()

        mock_dependencies["get_connections_use_case"].execute.return_value = GraphResultDTO(
            center=DocumentSummaryDTO(
                id=isolated_id,
                title="Isolated",
                path="isolated.md",
                word_count=10,
                link_count=0,
                backlink_count=0,
                tags=[],
                updated_at=datetime.now(),
            ),
            connections=[],
        )

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["get_connections"](
            vault_slug="my-vault",
            document_id=str(isolated_id),
        )

        assert result["center"]["id"] == str(isolated_id)
        assert result["connections"] == []


@pytest.mark.asyncio
class TestListDocumentsTool:
    """Tests for list_documents MCP tool."""

    async def test_list_documents_returns_paginated(
        self, mock_mcp, mock_dependencies, vault_id
    ):
        """Test listing documents returns paginated results."""
        doc_ids = [uuid4() for _ in range(3)]

        mock_dependencies["list_documents_use_case"].execute.return_value = (
            [
                DocumentSummaryDTO(
                    id=doc_ids[i],
                    title=f"Document {i}",
                    path=f"doc{i}.md",
                    word_count=100 * (i + 1),
                    link_count=i,
                    backlink_count=0,
                    tags=[f"tag{i}"],
                    updated_at=datetime.now(),
                )
                for i in range(3)
            ],
            3,  # total count
        )

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["list_documents"](
            vault_slug="my-vault",
            limit=10,
            offset=0,
        )

        assert "documents" in result
        assert len(result["documents"]) == 3
        assert result["total"] == 3
        assert result["limit"] == 10
        assert result["offset"] == 0

        # Verify document structure
        assert result["documents"][0]["id"] == str(doc_ids[0])
        assert result["documents"][0]["title"] == "Document 0"
        assert result["documents"][0]["word_count"] == 100

    async def test_list_documents_with_folder(self, mock_mcp, mock_dependencies, vault_id):
        """Test listing documents filtered by folder."""
        mock_dependencies["list_documents_use_case"].execute.return_value = ([], 0)

        register_mcp_tools(mock_mcp, mock_dependencies)
        await mock_mcp.tools["list_documents"](
            vault_slug="my-vault",
            folder="Projects",
        )

        # Verify folder filter was passed
        call_args = mock_dependencies["list_documents_use_case"].execute.call_args
        assert call_args[1]["folder"] == "Projects"

    async def test_list_documents_pagination(self, mock_mcp, mock_dependencies, vault_id):
        """Test listing documents with pagination."""
        mock_dependencies["list_documents_use_case"].execute.return_value = ([], 100)

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["list_documents"](
            vault_slug="my-vault",
            limit=20,
            offset=40,
        )

        assert result["limit"] == 20
        assert result["offset"] == 40
        assert result["total"] == 100

    async def test_list_documents_empty_vault(self, mock_mcp, mock_dependencies):
        """Test listing documents in empty vault."""
        mock_dependencies["list_documents_use_case"].execute.return_value = ([], 0)

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["list_documents"](
            vault_slug="empty-vault",
        )

        assert result["documents"] == []
        assert result["total"] == 0


# Structured Data Tools Tests

@pytest.mark.asyncio
class TestListTablesTool:
    """Tests for list_tables MCP tool."""

    async def test_list_tables_returns_paginated(
        self, mock_mcp, mock_dependencies, vault_id
    ):
        """Test listing tables returns paginated results."""
        table_ids = [uuid4() for _ in range(3)]

        mock_dependencies["list_tables_use_case"].execute.return_value = (
            [
                TableSummaryDTO(
                    id=table_ids[i],
                    name=f"Table {i}",
                    slug=f"table-{i}",
                    description=f"Description {i}",
                    column_count=i + 2,
                    row_count=(i + 1) * 10,
                    updated_at=datetime.now(),
                )
                for i in range(3)
            ],
            3,  # total count
        )

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["list_tables"](
            vault_slug="my-vault",
            limit=100,
            offset=0,
        )

        assert "tables" in result
        assert len(result["tables"]) == 3
        assert result["total"] == 3
        assert result["limit"] == 100
        assert result["offset"] == 0

        # Verify table structure
        assert result["tables"][0]["id"] == str(table_ids[0])
        assert result["tables"][0]["name"] == "Table 0"
        assert result["tables"][0]["row_count"] == 10

    async def test_list_tables_empty_vault(self, mock_mcp, mock_dependencies):
        """Test listing tables in vault with no tables."""
        mock_dependencies["list_tables_use_case"].execute.return_value = ([], 0)

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["list_tables"](
            vault_slug="empty-vault",
        )

        assert result["tables"] == []
        assert result["total"] == 0


@pytest.mark.asyncio
class TestGetTableTool:
    """Tests for get_table MCP tool."""

    async def test_get_table_returns_schema(self, mock_mcp, mock_dependencies, vault_id):
        """Test getting table returns schema details."""
        table_id = uuid4()

        mock_dependencies["get_table_use_case"].execute.return_value = TableDTO(
            id=table_id,
            name="Contacts",
            slug="contacts",
            description="Contact information",
            columns=[
                ColumnDTO(name="name", type="text", required=True),
                ColumnDTO(name="email", type="text", required=True, unique=True),
                ColumnDTO(name="age", type="number", required=False),
            ],
            row_count=150,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["get_table"](
            vault_slug="my-vault",
            table_slug="contacts",
        )

        assert result["id"] == str(table_id)
        assert result["name"] == "Contacts"
        assert result["slug"] == "contacts"
        assert result["description"] == "Contact information"
        assert len(result["columns"]) == 3
        assert result["columns"][0]["name"] == "name"
        assert result["columns"][0]["type"] == "text"
        assert result["columns"][0]["required"] is True
        assert result["row_count"] == 150


@pytest.mark.asyncio
class TestListTableRowsTool:
    """Tests for list_table_rows MCP tool."""

    async def test_list_rows_returns_paginated(
        self, mock_mcp, mock_dependencies, vault_id
    ):
        """Test listing rows returns paginated results."""
        table_id = uuid4()
        row_ids = [uuid4() for _ in range(3)]
        now = datetime.now()

        mock_dependencies["list_rows_use_case"].execute.return_value = (
            [
                RowDTO(
                    id=row_ids[i],
                    table_id=table_id,
                    data={"name": f"Item {i}", "value": i * 100},
                    created_at=now,
                    updated_at=now,
                )
                for i in range(3)
            ],
            3,  # total count
        )

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["list_table_rows"](
            vault_slug="my-vault",
            table_slug="items",
            limit=100,
            offset=0,
        )

        assert "rows" in result
        assert len(result["rows"]) == 3
        assert result["total"] == 3

        # Verify row structure
        assert result["rows"][0]["id"] == str(row_ids[0])
        assert result["rows"][0]["data"]["name"] == "Item 0"
        assert result["rows"][0]["data"]["value"] == 0

    async def test_list_rows_with_filters(self, mock_mcp, mock_dependencies, vault_id):
        """Test listing rows with filters."""
        mock_dependencies["list_rows_use_case"].execute.return_value = ([], 0)

        register_mcp_tools(mock_mcp, mock_dependencies)
        await mock_mcp.tools["list_table_rows"](
            vault_slug="my-vault",
            table_slug="items",
            filters={"status": "active"},
            sort_column="name",
            sort_order="asc",
        )

        # Verify filters were passed
        call_args = mock_dependencies["list_rows_use_case"].execute.call_args
        assert call_args[1]["filters"] == {"status": "active"}
        assert call_args[1]["sort_column"] == "name"
        assert call_args[1]["sort_order"] == "asc"

    async def test_list_rows_with_search(self, mock_mcp, mock_dependencies, vault_id):
        """Test listing rows with full-text search."""
        mock_dependencies["list_rows_use_case"].execute.return_value = ([], 0)

        register_mcp_tools(mock_mcp, mock_dependencies)
        await mock_mcp.tools["list_table_rows"](
            vault_slug="my-vault",
            table_slug="items",
            search_query="widget",
        )

        # Verify search was passed
        call_args = mock_dependencies["list_rows_use_case"].execute.call_args
        assert call_args[1]["search_query"] == "widget"


@pytest.mark.asyncio
class TestGetTableRowTool:
    """Tests for get_table_row MCP tool."""

    async def test_get_row_returns_data(self, mock_mcp, mock_dependencies, vault_id):
        """Test getting a specific row."""
        table_id = uuid4()
        row_id = uuid4()
        now = datetime.now()

        mock_dependencies["get_row_use_case"].execute.return_value = RowDTO(
            id=row_id,
            table_id=table_id,
            data={"name": "Widget", "price": 29.99, "active": True},
            created_at=now,
            updated_at=now,
        )

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["get_table_row"](
            vault_slug="my-vault",
            table_slug="products",
            row_id=str(row_id),
        )

        assert result["id"] == str(row_id)
        assert result["table_id"] == str(table_id)
        assert result["data"]["name"] == "Widget"
        assert result["data"]["price"] == 29.99
        assert result["data"]["active"] is True


@pytest.mark.asyncio
class TestQueryTableTool:
    """Tests for query_table MCP tool."""

    async def test_query_returns_results(self, mock_mcp, mock_dependencies, vault_id):
        """Test executing a query returns results."""
        mock_dependencies["execute_query_use_case"].execute.return_value = {
            "columns": ["name", "email"],
            "rows": [
                {"id": str(uuid4()), "name": "John", "email": "john@test.com"},
                {"id": str(uuid4()), "name": "Jane", "email": "jane@test.com"},
            ],
            "total": 2,
            "limit": 100,
            "offset": 0,
        }

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["query_table"](
            vault_slug="my-vault",
            query="TABLE name, email FROM contacts",
        )

        assert "columns" in result
        assert result["columns"] == ["name", "email"]
        assert "rows" in result
        assert len(result["rows"]) == 2
        assert result["rows"][0]["name"] == "John"
        assert result["total"] == 2

    async def test_query_with_filter(self, mock_mcp, mock_dependencies, vault_id):
        """Test executing a query with WHERE clause."""
        mock_dependencies["execute_query_use_case"].execute.return_value = {
            "columns": ["name", "status"],
            "rows": [
                {"id": str(uuid4()), "name": "Active Item", "status": "active"},
            ],
            "total": 1,
            "limit": 100,
            "offset": 0,
        }

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["query_table"](
            vault_slug="my-vault",
            query="TABLE name, status FROM items WHERE status = 'active'",
        )

        # Verify query was passed correctly
        call_args = mock_dependencies["execute_query_use_case"].execute.call_args
        assert "WHERE status = 'active'" in call_args[0][2]

        assert len(result["rows"]) == 1
        assert result["rows"][0]["status"] == "active"

    async def test_query_with_sort_and_limit(self, mock_mcp, mock_dependencies, vault_id):
        """Test executing a query with SORT and LIMIT."""
        mock_dependencies["execute_query_use_case"].execute.return_value = {
            "columns": ["name", "price"],
            "rows": [
                {"id": str(uuid4()), "name": "Expensive", "price": 999},
            ],
            "total": 100,
            "limit": 1,
            "offset": 0,
        }

        register_mcp_tools(mock_mcp, mock_dependencies)
        result = await mock_mcp.tools["query_table"](
            vault_slug="my-vault",
            query="TABLE * FROM products SORT price DESC LIMIT 1",
        )

        assert len(result["rows"]) == 1
        assert result["limit"] == 1
