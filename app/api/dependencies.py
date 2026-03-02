"""API dependencies for dependency injection."""

from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.domain.entities.user import User
from app.domain.exceptions import VaultNotFoundError
from app.infrastructure.database.connection import async_session_maker
from app.infrastructure.database.repositories import (
    PostgresDocumentLinkRepository,
    PostgresDocumentRepository,
    PostgresDocumentTableLinkRepository,
    PostgresEmbeddingChunkRepository,
    PostgresFolderRepository,
    PostgresRelationshipRepository,
    PostgresRowRepository,
    PostgresTableRepository,
    PostgresTagRepository,
    PostgresUserRepository,
    PostgresVaultRepository,
)
from app.infrastructure.embedding.openai_adapter import OpenAIEmbeddingAdapter
from app.infrastructure.age.graph_adapter import AgeGraphAdapter
from app.infrastructure.storage.local_storage import LocalStorageAdapter

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
        )
        if payload.get("type") != "access":
            raise credentials_exception
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    user_repo = PostgresUserRepository(session)
    user = await user_repo.get_by_id(UUID(user_id))

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


# Repository dependencies
def get_user_repository(session: SessionDep) -> PostgresUserRepository:
    """Get user repository."""
    return PostgresUserRepository(session)


def get_vault_repository(session: SessionDep) -> PostgresVaultRepository:
    """Get vault repository."""
    return PostgresVaultRepository(session)


def get_document_repository(session: SessionDep) -> PostgresDocumentRepository:
    """Get document repository."""
    return PostgresDocumentRepository(session)


def get_folder_repository(session: SessionDep) -> PostgresFolderRepository:
    """Get folder repository."""
    return PostgresFolderRepository(session)


def get_link_repository(session: SessionDep) -> PostgresDocumentLinkRepository:
    """Get document link repository."""
    return PostgresDocumentLinkRepository(session)


def get_tag_repository(session: SessionDep) -> PostgresTagRepository:
    """Get tag repository."""
    return PostgresTagRepository(session)


def get_embedding_repository(session: SessionDep) -> PostgresEmbeddingChunkRepository:
    """Get embedding chunk repository."""
    return PostgresEmbeddingChunkRepository(session)


def get_embedding_provider() -> OpenAIEmbeddingAdapter:
    """Get embedding provider."""
    return OpenAIEmbeddingAdapter()


def get_graph_provider(session: SessionDep) -> AgeGraphAdapter:
    """Get graph provider."""
    return AgeGraphAdapter(session)


def get_storage_provider() -> LocalStorageAdapter:
    """Get storage provider."""
    return LocalStorageAdapter()


def get_table_repository(session: SessionDep) -> PostgresTableRepository:
    """Get table repository."""
    return PostgresTableRepository(session)


def get_row_repository(session: SessionDep) -> PostgresRowRepository:
    """Get row repository."""
    return PostgresRowRepository(session)


def get_relationship_repository(session: SessionDep) -> PostgresRelationshipRepository:
    """Get relationship repository."""
    return PostgresRelationshipRepository(session)


def get_document_table_link_repository(
    session: SessionDep,
) -> PostgresDocumentTableLinkRepository:
    """Get document table link repository."""
    return PostgresDocumentTableLinkRepository(session)


UserRepoDep = Annotated[PostgresUserRepository, Depends(get_user_repository)]
VaultRepoDep = Annotated[PostgresVaultRepository, Depends(get_vault_repository)]
DocumentRepoDep = Annotated[PostgresDocumentRepository, Depends(get_document_repository)]
FolderRepoDep = Annotated[PostgresFolderRepository, Depends(get_folder_repository)]
LinkRepoDep = Annotated[PostgresDocumentLinkRepository, Depends(get_link_repository)]
TagRepoDep = Annotated[PostgresTagRepository, Depends(get_tag_repository)]
EmbeddingRepoDep = Annotated[PostgresEmbeddingChunkRepository, Depends(get_embedding_repository)]
EmbeddingProviderDep = Annotated[OpenAIEmbeddingAdapter, Depends(get_embedding_provider)]
GraphProviderDep = Annotated[AgeGraphAdapter, Depends(get_graph_provider)]
StorageProviderDep = Annotated[LocalStorageAdapter, Depends(get_storage_provider)]
TableRepoDep = Annotated[PostgresTableRepository, Depends(get_table_repository)]
RowRepoDep = Annotated[PostgresRowRepository, Depends(get_row_repository)]
RelationshipRepoDep = Annotated[PostgresRelationshipRepository, Depends(get_relationship_repository)]
DocumentTableLinkRepoDep = Annotated[PostgresDocumentTableLinkRepository, Depends(get_document_table_link_repository)]
