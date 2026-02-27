"""Vault routes."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
import io

from app.api.dependencies import (
    CurrentUserDep,
    DocumentRepoDep,
    EmbeddingProviderDep,
    EmbeddingRepoDep,
    FolderRepoDep,
    GraphProviderDep,
    LinkRepoDep,
    StorageProviderDep,
    TagRepoDep,
    VaultRepoDep,
)
from app.api.schemas.vault import (
    VaultCreate,
    VaultListResponse,
    VaultResponse,
    VaultUpdate,
)
from app.application.dto.vault_dto import VaultCreateDTO
from app.application.use_cases.vault import (
    CreateVaultUseCase,
    DeleteVaultUseCase,
    ExportVaultUseCase,
    GetVaultUseCase,
    IngestVaultUseCase,
    ListVaultsUseCase,
)
from app.domain.exceptions import DuplicateVaultError, VaultNotFoundError

router = APIRouter()


@router.get("", response_model=VaultListResponse)
async def list_vaults(
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
) -> VaultListResponse:
    """List all vaults for the current user."""
    use_case = ListVaultsUseCase(vault_repo)
    vaults = await use_case.execute(current_user.id)

    return VaultListResponse(
        vaults=[
            VaultResponse(
                id=v.id,
                name=v.name,
                slug=v.slug,
                description=v.description,
                document_count=v.document_count,
                created_at=v.created_at,
                updated_at=v.updated_at,
            )
            for v in vaults
        ]
    )


@router.post("", response_model=VaultResponse, status_code=status.HTTP_201_CREATED)
async def create_vault(
    data: VaultCreate,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
) -> VaultResponse:
    """Create a new vault."""
    use_case = CreateVaultUseCase(vault_repo)

    try:
        vault = await use_case.execute(
            current_user.id,
            VaultCreateDTO(name=data.name, description=data.description),
        )
    except DuplicateVaultError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return VaultResponse(
        id=vault.id,
        name=vault.name,
        slug=vault.slug,
        description=vault.description,
        document_count=vault.document_count,
        created_at=vault.created_at,
        updated_at=vault.updated_at,
    )


@router.get("/{slug}", response_model=VaultResponse)
async def get_vault(
    slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
) -> VaultResponse:
    """Get vault by slug."""
    use_case = GetVaultUseCase(vault_repo)

    try:
        vault = await use_case.execute(current_user.id, slug)
    except VaultNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return VaultResponse(
        id=vault.id,
        name=vault.name,
        slug=vault.slug,
        description=vault.description,
        document_count=vault.document_count,
        created_at=vault.created_at,
        updated_at=vault.updated_at,
    )


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vault(
    slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    storage_provider: StorageProviderDep,
) -> None:
    """Delete vault and all its contents."""
    use_case = DeleteVaultUseCase(vault_repo, storage_provider=storage_provider)

    try:
        await use_case.execute(current_user.id, slug)
    except VaultNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{slug}/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_vault(
    slug: str,
    file: UploadFile = File(...),
    generate_embeddings: bool = True,
    current_user: CurrentUserDep = None,
    vault_repo: VaultRepoDep = None,
    document_repo: DocumentRepoDep = None,
    folder_repo: FolderRepoDep = None,
    link_repo: LinkRepoDep = None,
    tag_repo: TagRepoDep = None,
    embedding_repo: EmbeddingRepoDep = None,
    embedding_provider: EmbeddingProviderDep = None,
    graph_provider: GraphProviderDep = None,
) -> dict:
    """Upload and ingest a ZIP file into a vault.

    If the vault doesn't exist, it will be created.
    """
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a ZIP archive",
        )

    # Read file content
    content = await file.read()

    use_case = IngestVaultUseCase(
        vault_repo=vault_repo,
        document_repo=document_repo,
        folder_repo=folder_repo,
        link_repo=link_repo,
        tag_repo=tag_repo,
        embedding_repo=embedding_repo if generate_embeddings else None,
        embedding_provider=embedding_provider if generate_embeddings else None,
        graph_provider=graph_provider,  # AGE graph building enabled
    )

    try:
        vault = await use_case.execute(
            user_id=current_user.id,
            vault_name=slug.replace("-", " ").title(),
            zip_content=content,
            generate_embeddings=generate_embeddings,
        )
    except DuplicateVaultError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vault '{slug}' already exists",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )

    return {
        "vault_id": str(vault.id),
        "status": "completed",
        "documents_count": vault.document_count,
        "message": "Vault ingestion completed",
    }


@router.get("/{slug}/export")
async def export_vault(
    slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    document_repo: DocumentRepoDep,
    folder_repo: FolderRepoDep,
) -> StreamingResponse:
    """Export vault as ZIP file."""
    use_case = ExportVaultUseCase(
        vault_repo=vault_repo,
        document_repo=document_repo,
        folder_repo=folder_repo,
    )

    try:
        zip_content = await use_case.execute(current_user.id, slug)
    except VaultNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return StreamingResponse(
        io.BytesIO(zip_content),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={slug}.zip"
        },
    )
