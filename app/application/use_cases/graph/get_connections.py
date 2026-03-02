"""Get connections use case."""

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.application.dto.document_dto import DocumentSummaryDTO
from app.application.interfaces.repositories import DocumentRepository, VaultRepository
from app.application.interfaces.graph_provider import GraphProvider
from app.application.use_cases.base import VaultAccessMixin
from app.domain.exceptions import DocumentNotFoundError


@dataclass
class ConnectionDTO:
    """DTO for a graph connection."""

    document: DocumentSummaryDTO
    distance: int
    link_type: str  # "incoming" or "outgoing"


@dataclass
class GraphResultDTO:
    """DTO for graph query result."""

    center: DocumentSummaryDTO
    connections: list[ConnectionDTO]


class GetConnectionsUseCase(VaultAccessMixin):
    """Use case for getting document connections in the graph."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        document_repo: DocumentRepository,
        graph_provider: GraphProvider,
    ) -> None:
        self.vault_repo = vault_repo
        self.document_repo = document_repo
        self.graph_provider = graph_provider
        self._logger = logging.getLogger(__name__)

    async def execute(
        self,
        user_id: UUID,
        vault_slug: str,
        document_id: UUID,
        depth: int = 2,
    ) -> GraphResultDTO:
        """Get document connections within N hops.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            document_id: Center document UUID
            depth: Maximum traversal depth (default: 2, max: 5)

        Returns:
            Graph result with center and connections

        Raises:
            VaultNotFoundError: If vault not found
            DocumentNotFoundError: If document not found
        """
        vault = await self.get_vault_or_raise(user_id, vault_slug)

        # Get center document
        document = await self.document_repo.get_by_id(document_id)
        if not document or document.vault_id != vault.id:
            raise DocumentNotFoundError(document_id=str(document_id))

        # Limit depth
        depth = min(depth, 5)

        # Get connections from graph
        graph_connections = await self.graph_provider.get_connections(
            document_id=document_id,
            vault_id=vault.id,
            depth=depth,
        )

        # Build connection DTOs
        connections = []
        for conn in graph_connections:
            conn_doc = await self.document_repo.get_by_id(UUID(conn["id"]))
            if conn_doc:
                connections.append(
                    ConnectionDTO(
                        document=DocumentSummaryDTO.from_entity(conn_doc),
                        distance=conn.get("distance", 1),
                        link_type=conn.get("link_type", "outgoing"),
                    )
                )

        self._logger.debug(f"Found {len(connections)} connections for document={document_id}")
        return GraphResultDTO(
            center=DocumentSummaryDTO.from_entity(document),
            connections=connections,
        )

    async def get_shortest_path(
        self,
        user_id: UUID,
        vault_slug: str,
        source_id: UUID,
        target_id: UUID,
    ) -> list[DocumentSummaryDTO] | None:
        """Get shortest path between two documents.

        Args:
            user_id: User ID
            vault_slug: Vault slug
            source_id: Start document UUID
            target_id: End document UUID

        Returns:
            List of documents in path, or None if no path exists
        """
        vault = await self.get_vault_or_raise(user_id, vault_slug)

        # Get path
        path = await self.graph_provider.get_shortest_path(
            source_id=source_id,
            target_id=target_id,
            vault_id=vault.id,
        )

        if not path:
            return None

        # Build document DTOs
        result = []
        for node in path:
            doc = await self.document_repo.get_by_id(UUID(node["id"]))
            if doc:
                result.append(DocumentSummaryDTO.from_entity(doc))

        self._logger.debug(f"Found path with {len(result)} nodes from {source_id} to {target_id}")
        return result
