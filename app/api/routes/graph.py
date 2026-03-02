"""Graph routes."""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.dependencies import (
    CurrentUserDep,
    DocumentRepoDep,
    GraphProviderDep,
    VaultRepoDep,
)
from app.api.schemas.document import DocumentSummaryResponse
from app.api.schemas.graph import (
    ConnectionResponse,
    GraphResponse,
    PathNodeResponse,
    PathResponse,
)
from app.application.use_cases.graph import GetConnectionsUseCase
from app.domain.exceptions import DomainException, VaultNotFoundError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/vaults/{slug}/graph/connections/{document_id}",
    response_model=GraphResponse,
)
async def get_connections(
    slug: str,
    document_id: UUID,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    document_repo: DocumentRepoDep,
    graph_provider: GraphProviderDep,
    depth: int = Query(default=2, ge=1, le=5),
) -> GraphResponse:
    """Get connected documents within N hops."""
    logger.debug(f"GET /vaults/{slug}/graph/connections/{document_id} depth={depth} user={current_user.id}")
    use_case = GetConnectionsUseCase(vault_repo, document_repo, graph_provider)

    result = await use_case.execute(
        current_user.id,
        slug,
        document_id,
        depth,
    )

    return GraphResponse(
        center=DocumentSummaryResponse(
            id=result.center.id,
            title=result.center.title,
            path=result.center.path,
            word_count=result.center.word_count,
            link_count=result.center.link_count,
            backlink_count=result.center.backlink_count,
            tags=result.center.tags,
            updated_at=result.center.updated_at,
        ),
        connections=[
            ConnectionResponse(
                document=DocumentSummaryResponse(
                    id=c.document.id,
                    title=c.document.title,
                    path=c.document.path,
                    word_count=c.document.word_count,
                    link_count=c.document.link_count,
                    backlink_count=c.document.backlink_count,
                    tags=c.document.tags,
                    updated_at=c.document.updated_at,
                ),
                distance=c.distance,
                link_type=c.link_type,
            )
            for c in result.connections
        ],
    )


@router.get(
    "/vaults/{slug}/graph/path",
    response_model=PathResponse,
)
async def get_shortest_path(
    slug: str,
    source: UUID,
    target: UUID,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    document_repo: DocumentRepoDep,
    graph_provider: GraphProviderDep,
) -> PathResponse:
    """Get shortest path between two documents."""
    logger.debug(f"GET /vaults/{slug}/graph/path source={source} target={target} user={current_user.id}")
    use_case = GetConnectionsUseCase(vault_repo, document_repo, graph_provider)

    path = await use_case.get_shortest_path(
        current_user.id,
        slug,
        source,
        target,
    )

    if path is None:
        class NoPathFoundError(DomainException):
            code = "NO_PATH_FOUND"
            http_status = 404

        raise NoPathFoundError("No path found between documents")

    return PathResponse(
        path=[
            PathNodeResponse(
                id=node.id,
                title=node.title,
                path=node.path,
            )
            for node in path
        ],
        length=len(path) - 1,
    )


@router.get("/vaults/{slug}/graph/orphans")
async def get_orphans(
    slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    graph_provider: GraphProviderDep,
) -> dict[str, Any]:
    """Get documents with no connections."""
    logger.debug(f"GET /vaults/{slug}/graph/orphans user={current_user.id}")
    vault = await vault_repo.get_by_slug(current_user.id, slug)
    if not vault:
        raise VaultNotFoundError(slug=slug)

    orphans = await graph_provider.get_orphans(vault.id)
    return {"orphans": orphans}


@router.get("/vaults/{slug}/graph/hubs")
async def get_hubs(
    slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    graph_provider: GraphProviderDep,
    limit: int = Query(default=10, ge=1, le=50),
) -> dict[str, Any]:
    """Get most connected documents."""
    logger.debug(f"GET /vaults/{slug}/graph/hubs limit={limit} user={current_user.id}")
    vault = await vault_repo.get_by_slug(current_user.id, slug)
    if not vault:
        raise VaultNotFoundError(slug=slug)

    hubs = await graph_provider.get_hubs(vault.id, limit)
    return {"hubs": hubs}
