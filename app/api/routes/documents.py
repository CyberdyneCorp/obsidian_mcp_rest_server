"""Document routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import (
    CurrentUserDep,
    DocumentRepoDep,
    FolderRepoDep,
    LinkRepoDep,
    VaultRepoDep,
)
from app.api.schemas.document import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    DocumentSummaryResponse,
    DocumentUpdate,
)
from app.api.schemas.link import (
    BacklinkResponse,
    BacklinksResponse,
    BacklinkSourceResponse,
    LinkResponse,
    LinksResponse,
    LinkTargetResponse,
)
from app.application.dto.document_dto import DocumentCreateDTO, DocumentUpdateDTO
from app.application.use_cases.document import (
    CreateDocumentUseCase,
    DeleteDocumentUseCase,
    GetDocumentUseCase,
    ListDocumentsUseCase,
    UpdateDocumentUseCase,
)
from app.application.use_cases.link import (
    GetBacklinksUseCase,
    GetOutgoingLinksUseCase,
)
from app.domain.exceptions import (
    DocumentNotFoundError,
    DuplicateDocumentError,
    VaultNotFoundError,
)

router = APIRouter()


@router.get("/vaults/{slug}/documents", response_model=DocumentListResponse)
async def list_documents(
    slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    document_repo: DocumentRepoDep,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    folder: str | None = None,
    tag: str | None = None,
) -> DocumentListResponse:
    """List documents in a vault."""
    use_case = ListDocumentsUseCase(vault_repo, document_repo)

    try:
        documents, total = await use_case.execute(
            current_user.id,
            slug,
            limit=limit,
            offset=offset,
            folder=folder,
            tag=tag,
        )
    except VaultNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return DocumentListResponse(
        documents=[
            DocumentSummaryResponse(
                id=d.id,
                title=d.title,
                path=d.path,
                word_count=d.word_count,
                link_count=d.link_count,
                backlink_count=d.backlink_count,
                tags=d.tags,
                updated_at=d.updated_at,
            )
            for d in documents
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/vaults/{slug}/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    slug: str,
    document_id: UUID,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    document_repo: DocumentRepoDep,
) -> DocumentResponse:
    """Get document by ID."""
    use_case = GetDocumentUseCase(vault_repo, document_repo)

    try:
        doc = await use_case.execute(current_user.id, slug, document_id=document_id)
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

    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        path=doc.path,
        content=doc.content,
        frontmatter=doc.frontmatter,
        tags=doc.tags,
        aliases=doc.aliases,
        word_count=doc.word_count,
        link_count=doc.link_count,
        backlink_count=doc.backlink_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.post(
    "/vaults/{slug}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    slug: str,
    data: DocumentCreate,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    document_repo: DocumentRepoDep,
    folder_repo: FolderRepoDep,
) -> DocumentResponse:
    """Create a new document."""
    use_case = CreateDocumentUseCase(vault_repo, document_repo, folder_repo)

    try:
        doc = await use_case.execute(
            current_user.id,
            slug,
            DocumentCreateDTO(
                path=data.path,
                content=data.content,
                frontmatter=data.frontmatter or {},
            ),
        )
    except VaultNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except DuplicateDocumentError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        path=doc.path,
        content=doc.content,
        frontmatter=doc.frontmatter,
        tags=doc.tags,
        aliases=doc.aliases,
        word_count=doc.word_count,
        link_count=doc.link_count,
        backlink_count=doc.backlink_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.patch("/vaults/{slug}/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    slug: str,
    document_id: UUID,
    data: DocumentUpdate,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    document_repo: DocumentRepoDep,
    link_repo: LinkRepoDep,
) -> DocumentResponse:
    """Update a document."""
    use_case = UpdateDocumentUseCase(vault_repo, document_repo, link_repo)

    try:
        doc = await use_case.execute(
            current_user.id,
            slug,
            document_id,
            DocumentUpdateDTO(
                content=data.content,
                frontmatter=data.frontmatter,
            ),
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

    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        path=doc.path,
        content=doc.content,
        frontmatter=doc.frontmatter,
        tags=doc.tags,
        aliases=doc.aliases,
        word_count=doc.word_count,
        link_count=doc.link_count,
        backlink_count=doc.backlink_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.delete(
    "/vaults/{slug}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    slug: str,
    document_id: UUID,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    document_repo: DocumentRepoDep,
    link_repo: LinkRepoDep,
) -> None:
    """Delete a document."""
    use_case = DeleteDocumentUseCase(vault_repo, document_repo, link_repo)

    try:
        await use_case.execute(current_user.id, slug, document_id)
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


@router.get(
    "/vaults/{slug}/documents/{document_id}/links/outgoing",
    response_model=LinksResponse,
)
async def get_outgoing_links(
    slug: str,
    document_id: UUID,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    document_repo: DocumentRepoDep,
    link_repo: LinkRepoDep,
) -> LinksResponse:
    """Get outgoing links from a document."""
    use_case = GetOutgoingLinksUseCase(vault_repo, document_repo, link_repo)

    try:
        links = await use_case.execute(current_user.id, slug, document_id)
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

    return LinksResponse(
        links=[
            LinkResponse(
                id=link.id,
                link_text=link.link_text,
                display_text=link.display_text,
                link_type=link.link_type,
                is_resolved=link.is_resolved,
                target_document=LinkTargetResponse(
                    id=link.target_document.id,
                    title=link.target_document.title,
                    path=link.target_document.path,
                )
                if link.target_document
                else None,
            )
            for link in links
        ]
    )


@router.get(
    "/vaults/{slug}/documents/{document_id}/links/incoming",
    response_model=BacklinksResponse,
)
async def get_backlinks(
    slug: str,
    document_id: UUID,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    document_repo: DocumentRepoDep,
    link_repo: LinkRepoDep,
) -> BacklinksResponse:
    """Get backlinks (incoming links) to a document."""
    use_case = GetBacklinksUseCase(vault_repo, document_repo, link_repo)

    try:
        backlinks = await use_case.execute(current_user.id, slug, document_id)
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

    return BacklinksResponse(
        backlinks=[
            BacklinkResponse(
                document=BacklinkSourceResponse(
                    id=bl.document.id,
                    title=bl.document.title,
                    path=bl.document.path,
                ),
                link_text=bl.link_text,
                context=bl.context,
            )
            for bl in backlinks
        ]
    )
