"""Data Transfer Objects for the application layer."""

from app.application.dto.vault_dto import VaultDTO, VaultCreateDTO, VaultUpdateDTO
from app.application.dto.document_dto import (
    DocumentDTO,
    DocumentCreateDTO,
    DocumentUpdateDTO,
    DocumentSummaryDTO,
)
from app.application.dto.search_dto import SearchResultDTO, SearchQueryDTO
from app.application.dto.link_dto import LinkDTO, BacklinkDTO
from app.application.dto.auth_dto import (
    UserDTO,
    UserCreateDTO,
    TokenDTO,
    LoginDTO,
)

__all__ = [
    "BacklinkDTO",
    "DocumentCreateDTO",
    "DocumentDTO",
    "DocumentSummaryDTO",
    "DocumentUpdateDTO",
    "LinkDTO",
    "LoginDTO",
    "SearchQueryDTO",
    "SearchResultDTO",
    "TokenDTO",
    "UserCreateDTO",
    "UserDTO",
    "VaultCreateDTO",
    "VaultDTO",
    "VaultUpdateDTO",
]
