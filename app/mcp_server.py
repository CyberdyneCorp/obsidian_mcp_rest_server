"""FastMCP server for Obsidian Vault."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastmcp import FastMCP

from app.config import get_settings
from app.infrastructure.database.connection import async_session_maker
from app.infrastructure.database.repositories import (
    PostgresDocumentLinkRepository,
    PostgresDocumentRepository,
    PostgresEmbeddingChunkRepository,
    PostgresFolderRepository,
    PostgresTagRepository,
    PostgresUserRepository,
    PostgresVaultRepository,
)
from app.infrastructure.embedding.openai_adapter import OpenAIEmbeddingAdapter
from app.infrastructure.age.graph_adapter import AgeGraphAdapter
from app.application.dto.search_dto import SearchQueryDTO
from app.application.use_cases.document import GetDocumentUseCase, ListDocumentsUseCase
from app.application.use_cases.link import GetBacklinksUseCase
from app.application.use_cases.search import SemanticSearchUseCase, FulltextSearchUseCase
from app.application.use_cases.vault import ListVaultsUseCase
from app.application.use_cases.graph import GetConnectionsUseCase
from uuid import UUID

logger = logging.getLogger(__name__)
settings = get_settings()

# Create FastMCP server
mcp = FastMCP(
    name="Obsidian Vault Server",
    version="0.1.0",
    description="MCP server for Obsidian vault management with semantic search and knowledge graph",
)


@asynccontextmanager
async def get_dependencies():
    """Get dependencies for MCP tools."""
    async with async_session_maker() as session:
        yield {
            "session": session,
            "vault_repo": PostgresVaultRepository(session),
            "document_repo": PostgresDocumentRepository(session),
            "folder_repo": PostgresFolderRepository(session),
            "link_repo": PostgresDocumentLinkRepository(session),
            "tag_repo": PostgresTagRepository(session),
            "embedding_repo": PostgresEmbeddingChunkRepository(session),
            "embedding_provider": OpenAIEmbeddingAdapter(),
            "graph_provider": AgeGraphAdapter(session),
        }


# MCP Tools
@mcp.tool()
async def list_vaults(user_id: str) -> list[dict]:
    """List all vaults for a user.

    Args:
        user_id: The user's UUID

    Returns:
        List of vault objects with id, name, slug, and document_count
    """
    async with get_dependencies() as deps:
        use_case = ListVaultsUseCase(deps["vault_repo"])
        vaults = await use_case.execute(UUID(user_id))

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
    user_id: str,
    vault_slug: str,
    path: str | None = None,
    document_id: str | None = None,
) -> dict:
    """Get a document by path or ID.

    Args:
        user_id: The user's UUID
        vault_slug: The vault slug
        path: Document path (e.g., "Notes/My Document.md")
        document_id: Document UUID (alternative to path)

    Returns:
        Document object with id, title, path, content, frontmatter, and tags
    """
    async with get_dependencies() as deps:
        use_case = GetDocumentUseCase(deps["vault_repo"], deps["document_repo"])

        doc_uuid = UUID(document_id) if document_id else None
        doc = await use_case.execute(UUID(user_id), vault_slug, document_id=doc_uuid, path=path)

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
    user_id: str,
    vault_slug: str,
    query: str,
    search_type: str = "semantic",
    limit: int = 10,
    folder: str | None = None,
    tags: list[str] | None = None,
) -> list[dict]:
    """Search documents using semantic or full-text search.

    Args:
        user_id: The user's UUID
        vault_slug: The vault slug
        query: Search query text
        search_type: "semantic" for vector search or "fulltext" for text search
        limit: Maximum number of results (default: 10)
        folder: Optional folder path to filter results
        tags: Optional list of tags to filter results

    Returns:
        List of search results with document info and relevance score
    """
    async with get_dependencies() as deps:
        if search_type == "semantic":
            use_case = SemanticSearchUseCase(
                vault_repo=deps["vault_repo"],
                document_repo=deps["document_repo"],
                embedding_repo=deps["embedding_repo"],
                embedding_provider=deps["embedding_provider"],
            )
            search_query = SearchQueryDTO(
                query=query,
                limit=limit,
                folder=folder,
                tags=tags or [],
            )
            results = await use_case.execute(UUID(user_id), vault_slug, search_query)
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
            use_case_ft = FulltextSearchUseCase(deps["vault_repo"], deps["document_repo"])
            results = await use_case_ft.execute(UUID(user_id), vault_slug, query, limit, folder)
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
    user_id: str,
    vault_slug: str,
    document_id: str,
) -> list[dict]:
    """Get documents that link to a specific document.

    Args:
        user_id: The user's UUID
        vault_slug: The vault slug
        document_id: Document UUID

    Returns:
        List of backlinks with source document info and link context
    """
    async with get_dependencies() as deps:
        use_case = GetBacklinksUseCase(
            deps["vault_repo"],
            deps["document_repo"],
            deps["link_repo"],
        )
        backlinks = await use_case.execute(UUID(user_id), vault_slug, UUID(document_id))

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
    user_id: str,
    vault_slug: str,
    document_id: str,
    depth: int = 2,
) -> dict:
    """Get the document graph around a document.

    Args:
        user_id: The user's UUID
        vault_slug: The vault slug
        document_id: Document UUID
        depth: Traversal depth (default: 2, max: 5)

    Returns:
        Graph with center document and list of connected documents
    """
    async with get_dependencies() as deps:
        use_case = GetConnectionsUseCase(
            deps["vault_repo"],
            deps["document_repo"],
            deps["graph_provider"],
        )
        result = await use_case.execute(UUID(user_id), vault_slug, UUID(document_id), depth)

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
    user_id: str,
    vault_slug: str,
    limit: int = 50,
    offset: int = 0,
    folder: str | None = None,
) -> dict:
    """List documents in a vault.

    Args:
        user_id: The user's UUID
        vault_slug: The vault slug
        limit: Maximum number of results (default: 50)
        offset: Pagination offset
        folder: Optional folder path to filter

    Returns:
        Object with documents list and total count
    """
    async with get_dependencies() as deps:
        use_case = ListDocumentsUseCase(deps["vault_repo"], deps["document_repo"])
        docs, total = await use_case.execute(
            UUID(user_id), vault_slug, limit=limit, offset=offset, folder=folder
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


def main():
    """Run the MCP server."""
    import uvicorn

    logger.info("Starting MCP server...")
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()
