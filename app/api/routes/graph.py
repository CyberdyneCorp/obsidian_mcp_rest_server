"""Graph routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

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
from app.domain.exceptions import DocumentNotFoundError, VaultNotFoundError

router = APIRouter()


@router.get(
    "/vaults/{slug}/graph/connections/{document_id}",
    response_model=GraphResponse,
)
async def get_connections(
    slug: str,
    document_id: UUID,
    depth: int = Query(default=2, ge=1, le=5),
    current_user: CurrentUserDep = None,
    vault_repo: VaultRepoDep = None,
    document_repo: DocumentRepoDep = None,
    graph_provider: GraphProviderDep = None,
) -> GraphResponse:
    """Get connected documents within N hops."""
    use_case = GetConnectionsUseCase(vault_repo, document_repo, graph_provider)

    try:
        result = await use_case.execute(
            current_user.id,
            slug,
            document_id,
            depth,
        )
    except VaultNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
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
    current_user: CurrentUserDep = None,
    vault_repo: VaultRepoDep = None,
    document_repo: DocumentRepoDep = None,
    graph_provider: GraphProviderDep = None,
) -> PathResponse:
    """Get shortest path between two documents."""
    use_case = GetConnectionsUseCase(vault_repo, document_repo, graph_provider)

    try:
        path = await use_case.get_shortest_path(
            current_user.id,
            slug,
            source,
            target,
        )
    except VaultNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No path found between documents",
        )

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
) -> dict:
    """Get documents with no connections."""
    vault = await vault_repo.get_by_slug(current_user.id, slug)
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vault '{slug}' not found",
        )

    try:
        orphans = await graph_provider.get_orphans(vault.id)
        return {"orphans": orphans}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph query failed: {str(e)}",
        )


@router.get("/vaults/{slug}/graph/hubs")
async def get_hubs(
    slug: str,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: CurrentUserDep = None,
    vault_repo: VaultRepoDep = None,
    graph_provider: GraphProviderDep = None,
) -> dict:
    """Get most connected documents."""
    vault = await vault_repo.get_by_slug(current_user.id, slug)
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vault '{slug}' not found",
        )

    try:
        hubs = await graph_provider.get_hubs(vault.id, limit)
        return {"hubs": hubs}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph query failed: {str(e)}",
        )
