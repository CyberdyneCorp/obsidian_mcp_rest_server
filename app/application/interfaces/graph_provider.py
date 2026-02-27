"""Graph provider port interface for Apache AGE."""

from typing import Any, Protocol
from uuid import UUID


class GraphProvider(Protocol):
    """Port interface for knowledge graph operations using Apache AGE."""

    async def create_document_node(
        self,
        document_id: UUID,
        vault_id: UUID,
        title: str,
        path: str,
    ) -> None:
        """Create a document node in the graph.

        Args:
            document_id: Document UUID
            vault_id: Vault UUID
            title: Document title
            path: Document path
        """
        ...

    async def delete_document_node(self, document_id: UUID) -> None:
        """Delete a document node and all its edges.

        Args:
            document_id: Document UUID to delete
        """
        ...

    async def create_link_edge(
        self,
        source_id: UUID,
        target_id: UUID,
        link_type: str,
        display_text: str | None = None,
    ) -> None:
        """Create a link edge between documents.

        Args:
            source_id: Source document UUID
            target_id: Target document UUID
            link_type: Type of link (wikilink, embed, etc.)
            display_text: Optional display text for the link
        """
        ...

    async def delete_link_edge(
        self,
        source_id: UUID,
        target_id: UUID,
    ) -> None:
        """Delete a link edge between documents.

        Args:
            source_id: Source document UUID
            target_id: Target document UUID
        """
        ...

    async def delete_outgoing_edges(self, source_id: UUID) -> int:
        """Delete all outgoing edges from a document.

        Args:
            source_id: Source document UUID

        Returns:
            Number of edges deleted
        """
        ...

    async def get_connections(
        self,
        document_id: UUID,
        vault_id: UUID,
        depth: int = 2,
    ) -> list[dict[str, Any]]:
        """Get connected documents within N hops.

        Args:
            document_id: Center document UUID
            vault_id: Vault UUID
            depth: Maximum traversal depth

        Returns:
            List of connected document info dicts
        """
        ...

    async def get_shortest_path(
        self,
        source_id: UUID,
        target_id: UUID,
        vault_id: UUID,
    ) -> list[dict[str, Any]] | None:
        """Get shortest path between two documents.

        Args:
            source_id: Start document UUID
            target_id: End document UUID
            vault_id: Vault UUID

        Returns:
            List of documents in path, or None if no path exists
        """
        ...

    async def get_orphans(self, vault_id: UUID) -> list[dict[str, Any]]:
        """Get documents with no connections.

        Args:
            vault_id: Vault UUID

        Returns:
            List of orphan document info dicts
        """
        ...

    async def get_hubs(
        self,
        vault_id: UUID,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get most connected documents.

        Args:
            vault_id: Vault UUID
            limit: Maximum number of results

        Returns:
            List of document info dicts with connection counts
        """
        ...
