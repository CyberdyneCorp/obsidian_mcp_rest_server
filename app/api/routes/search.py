"""Search routes."""

import logging

from fastapi import APIRouter, Query

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

router = APIRouter()
logger = logging.getLogger(__name__)


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
    logger.debug(f"POST /vaults/{slug}/search/semantic query={data.query!r} user={current_user.id}")
    use_case = SemanticSearchUseCase(
        vault_repo=vault_repo,
        document_repo=document_repo,
        embedding_repo=embedding_repo,
        embedding_provider=embedding_provider,
    )

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

    logger.debug(f"Semantic search returned {len(results)} results")
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
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    document_repo: DocumentRepoDep,
    q: str = Query(..., min_length=1, max_length=1000),
    limit: int = Query(default=20, ge=1, le=100),
    folder: str | None = None,
) -> FulltextSearchResponse:
    """Perform full-text search."""
    logger.debug(f"GET /vaults/{slug}/search/fulltext q={q!r} user={current_user.id}")
    use_case = FulltextSearchUseCase(vault_repo, document_repo)

    results = await use_case.execute(
        current_user.id,
        slug,
        q,
        limit,
        folder,
    )

    logger.debug(f"Fulltext search returned {len(results)} results")
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
