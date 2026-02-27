"""Search routes."""

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import (
    CurrentUserDep,
    DocumentRepoDep,
    EmbeddingProviderDep,
    EmbeddingRepoDep,
    VaultRepoDep,
)
from app.api.schemas.document import DocumentSummaryResponse
from app.api.schemas.search import (
    FulltextSearchResponse,
    FulltextSearchResult,
    SearchResultResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
)
from app.application.dto.search_dto import SearchQueryDTO
from app.application.use_cases.search import FulltextSearchUseCase, SemanticSearchUseCase
from app.domain.exceptions import EmbeddingServiceError, VaultNotFoundError

router = APIRouter()


@router.post(
    "/vaults/{slug}/search/semantic",
    response_model=SemanticSearchResponse,
)
async def semantic_search(
    slug: str,
    data: SemanticSearchRequest,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    document_repo: DocumentRepoDep,
    embedding_repo: EmbeddingRepoDep,
    embedding_provider: EmbeddingProviderDep,
) -> SemanticSearchResponse:
    """Perform semantic (vector) search."""
    use_case = SemanticSearchUseCase(
        vault_repo=vault_repo,
        document_repo=document_repo,
        embedding_repo=embedding_repo,
        embedding_provider=embedding_provider,
    )

    try:
        results = await use_case.execute(
            current_user.id,
            slug,
            SearchQueryDTO(
                query=data.query,
                limit=data.limit,
                threshold=data.threshold,
                folder=data.folder,
                tags=data.tags or [],
            ),
        )
    except VaultNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except EmbeddingServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    return SemanticSearchResponse(
        results=[
            SearchResultResponse(
                document=DocumentSummaryResponse(
                    id=r.document.id,
                    title=r.document.title,
                    path=r.document.path,
                    word_count=r.document.word_count,
                    link_count=r.document.link_count,
                    backlink_count=r.document.backlink_count,
                    tags=r.document.tags,
                    updated_at=r.document.updated_at,
                ),
                score=r.score,
                matched_chunk=r.matched_chunk,
            )
            for r in results
        ],
        query=data.query,
        total=len(results),
    )


@router.get(
    "/vaults/{slug}/search/fulltext",
    response_model=FulltextSearchResponse,
)
async def fulltext_search(
    slug: str,
    q: str = Query(..., min_length=1, max_length=1000),
    limit: int = Query(default=20, ge=1, le=100),
    folder: str | None = None,
    current_user: CurrentUserDep = None,
    vault_repo: VaultRepoDep = None,
    document_repo: DocumentRepoDep = None,
) -> FulltextSearchResponse:
    """Perform full-text search."""
    use_case = FulltextSearchUseCase(vault_repo, document_repo)

    try:
        results = await use_case.execute(
            current_user.id,
            slug,
            q,
            limit,
            folder,
        )
    except VaultNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return FulltextSearchResponse(
        results=[
            FulltextSearchResult(
                document=DocumentSummaryResponse(
                    id=r.document.id,
                    title=r.document.title,
                    path=r.document.path,
                    word_count=r.document.word_count,
                    link_count=r.document.link_count,
                    backlink_count=r.document.backlink_count,
                    tags=r.document.tags,
                    updated_at=r.document.updated_at,
                ),
                headline=r.headline,
            )
            for r in results
        ],
        query=q,
    )
