"""MCP tool definitions."""

import logging
from typing import Any
from uuid import UUID

from fastmcp import FastMCP

from app.application.dto.search_dto import SearchQueryDTO
from app.application.use_cases.document import GetDocumentUseCase, ListDocumentsUseCase
from app.application.use_cases.link import GetBacklinksUseCase
from app.application.use_cases.search import SemanticSearchUseCase, FulltextSearchUseCase
from app.application.use_cases.vault import ListVaultsUseCase
from app.application.use_cases.graph import GetConnectionsUseCase

logger = logging.getLogger(__name__)


def register_mcp_tools(mcp: FastMCP, dependencies: dict[str, Any]) -> None:
    """Register all MCP tools with the server.

    Args:
        mcp: FastMCP server instance
        dependencies: Dictionary of use case dependencies
    """

    @mcp.tool()
    async def list_vaults() -> list[dict]:
        """List all vaults for the authenticated user.

        Returns:
            List of vault objects with id, name, slug, and document_count
        """
        use_case: ListVaultsUseCase = dependencies["list_vaults_use_case"]
        user_id: UUID = dependencies["current_user_id"]

        vaults = await use_case.execute(user_id)
        return [
            {
                "id": str(v.id),
                "name": v.name,
                "slug": v.slug,
                "document_count": v.document_count,
            }
            for v in vaults
        ]

    @mcp.tool()
    async def get_document(
        vault_slug: str,
        path: str | None = None,
        document_id: str | None = None,
    ) -> dict:
        """Get a document by path or ID.

        Args:
            vault_slug: The vault slug
            path: Document path (e.g., "Notes/My Document.md")
            document_id: Document UUID (alternative to path)

        Returns:
            Document object with id, title, path, content, frontmatter, and tags
        """
        use_case: GetDocumentUseCase = dependencies["get_document_use_case"]
        user_id: UUID = dependencies["current_user_id"]

        doc_uuid = UUID(document_id) if document_id else None
        doc = await use_case.execute(user_id, vault_slug, document_id=doc_uuid, path=path)

        return {
            "id": str(doc.id),
            "title": doc.title,
            "path": doc.path,
            "content": doc.content,
            "frontmatter": doc.frontmatter,
            "tags": doc.tags,
            "word_count": doc.word_count,
        }

    @mcp.tool()
    async def search_documents(
        vault_slug: str,
        query: str,
        search_type: str = "semantic",
        limit: int = 10,
        folder: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict]:
        """Search documents using semantic or full-text search.

        Args:
            vault_slug: The vault slug
            query: Search query text
            search_type: "semantic" for vector search or "fulltext" for text search
            limit: Maximum number of results (default: 10)
            folder: Optional folder path to filter results
            tags: Optional list of tags to filter results

        Returns:
            List of search results with document info and relevance score
        """
        user_id: UUID = dependencies["current_user_id"]

        if search_type == "semantic":
            use_case: SemanticSearchUseCase = dependencies["semantic_search_use_case"]
            search_query = SearchQueryDTO(
                query=query,
                limit=limit,
                folder=folder,
                tags=tags or [],
            )
            results = await use_case.execute(user_id, vault_slug, search_query)
            return [
                {
                    "id": str(r.document.id),
                    "title": r.document.title,
                    "path": r.document.path,
                    "score": r.score,
                    "matched_chunk": r.matched_chunk,
                }
                for r in results
            ]
        else:
            use_case_ft: FulltextSearchUseCase = dependencies["fulltext_search_use_case"]
            results = await use_case_ft.execute(user_id, vault_slug, query, limit, folder)
            return [
                {
                    "id": str(r.document.id),
                    "title": r.document.title,
                    "path": r.document.path,
                    "headline": r.headline,
                }
                for r in results
            ]

    @mcp.tool()
    async def get_backlinks(
        vault_slug: str,
        document_id: str,
    ) -> list[dict]:
        """Get documents that link to a specific document.

        Args:
            vault_slug: The vault slug
            document_id: Document UUID

        Returns:
            List of backlinks with source document info and link context
        """
        use_case: GetBacklinksUseCase = dependencies["get_backlinks_use_case"]
        user_id: UUID = dependencies["current_user_id"]

        backlinks = await use_case.execute(user_id, vault_slug, UUID(document_id))
        return [
            {
                "document": {
                    "id": str(bl.document.id),
                    "title": bl.document.title,
                    "path": bl.document.path,
                },
                "link_text": bl.link_text,
                "context": bl.context,
            }
            for bl in backlinks
        ]

    @mcp.tool()
    async def get_connections(
        vault_slug: str,
        document_id: str,
        depth: int = 2,
    ) -> dict:
        """Get the document graph around a document.

        Args:
            vault_slug: The vault slug
            document_id: Document UUID
            depth: Traversal depth (default: 2, max: 5)

        Returns:
            Graph with center document and list of connected documents
        """
        use_case: GetConnectionsUseCase = dependencies["get_connections_use_case"]
        user_id: UUID = dependencies["current_user_id"]

        result = await use_case.execute(user_id, vault_slug, UUID(document_id), depth)
        return {
            "center": {
                "id": str(result.center.id),
                "title": result.center.title,
                "path": result.center.path,
            },
            "connections": [
                {
                    "id": str(c.document.id),
                    "title": c.document.title,
                    "path": c.document.path,
                    "distance": c.distance,
                    "link_type": c.link_type,
                }
                for c in result.connections
            ],
        }

    @mcp.tool()
    async def list_documents(
        vault_slug: str,
        limit: int = 50,
        offset: int = 0,
        folder: str | None = None,
    ) -> dict:
        """List documents in a vault.

        Args:
            vault_slug: The vault slug
            limit: Maximum number of results (default: 50)
            offset: Pagination offset
            folder: Optional folder path to filter

        Returns:
            Object with documents list and total count
        """
        use_case: ListDocumentsUseCase = dependencies["list_documents_use_case"]
        user_id: UUID = dependencies["current_user_id"]

        docs, total = await use_case.execute(
            user_id, vault_slug, limit=limit, offset=offset, folder=folder
        )
        return {
            "documents": [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "path": d.path,
                    "word_count": d.word_count,
                    "tags": d.tags,
                }
                for d in docs
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
