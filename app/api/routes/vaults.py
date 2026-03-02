"""Vault routes."""

import io
import logging
from typing import Any

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import StreamingResponse

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
from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get("", response_model=VaultListResponse)
async def list_vaults(
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
) -> VaultListResponse:
    """List all vaults for the current user."""
    logger.debug(f"GET /vaults user={current_user.id}")
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
    logger.info(f"POST /vaults name={data.name} user={current_user.id}")
    use_case = CreateVaultUseCase(vault_repo)

    vault = await use_case.execute(
        current_user.id,
        VaultCreateDTO(name=data.name, description=data.description),
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
    logger.debug(f"GET /vaults/{slug} user={current_user.id}")
    use_case = GetVaultUseCase(vault_repo)

    vault = await use_case.execute(current_user.id, slug)

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
    logger.info(f"DELETE /vaults/{slug} user={current_user.id}")
    use_case = DeleteVaultUseCase(vault_repo, storage_provider=storage_provider)

    await use_case.execute(current_user.id, slug)


@router.post("/{slug}/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_vault(
    slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    document_repo: DocumentRepoDep,
    folder_repo: FolderRepoDep,
    link_repo: LinkRepoDep,
    tag_repo: TagRepoDep,
    embedding_repo: EmbeddingRepoDep,
    embedding_provider: EmbeddingProviderDep,
    graph_provider: GraphProviderDep,
    file: UploadFile = File(...),
    generate_embeddings: bool = True,
) -> dict[str, Any]:
    """Upload and ingest a ZIP file into a vault.

    If the vault doesn't exist, it will be created.
    """
    logger.info(f"POST /vaults/{slug}/ingest file={file.filename} user={current_user.id}")

    if not file.filename or not file.filename.endswith(".zip"):
        from app.domain.exceptions import DomainException

        class InvalidFileError(DomainException):
            code = "INVALID_FILE"
            http_status = 400

        raise InvalidFileError("File must be a ZIP archive")

    # Read file content
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        from app.domain.exceptions import DomainException

        class FileTooLargeError(DomainException):
            code = "FILE_TOO_LARGE"
            http_status = 413

        raise FileTooLargeError(
            f"File exceeds maximum size of {settings.max_upload_size_mb}MB"
        )

    use_case = IngestVaultUseCase(
        vault_repo=vault_repo,
        document_repo=document_repo,
        folder_repo=folder_repo,
        link_repo=link_repo,
        tag_repo=tag_repo,
        embedding_repo=embedding_repo if generate_embeddings else None,
        embedding_provider=embedding_provider if generate_embeddings else None,
        graph_provider=graph_provider,
    )

    vault = await use_case.execute(
        user_id=current_user.id,
        vault_name=slug.replace("-", " ").title(),
        zip_content=content,
        generate_embeddings=generate_embeddings,
    )

    logger.info(f"Vault ingestion completed slug={slug} docs={vault.document_count}")
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
    logger.debug(f"GET /vaults/{slug}/export user={current_user.id}")
    use_case = ExportVaultUseCase(
        vault_repo=vault_repo,
        document_repo=document_repo,
        folder_repo=folder_repo,
    )

    zip_content = await use_case.execute(current_user.id, slug)

    return StreamingResponse(
        io.BytesIO(zip_content),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={slug}.zip"
        },
    )
