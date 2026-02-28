"""Domain exceptions."""

from typing import Any


class DomainException(Exception):
    """Base domain exception."""

    code: str = "DOMAIN_ERROR"
    http_status: int = 400

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary."""
        result: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


# Vault Exceptions
class VaultNotFoundError(DomainException):
    """Vault does not exist."""

    code = "VAULT_NOT_FOUND"
    http_status = 404

    def __init__(self, vault_id: str | None = None, slug: str | None = None) -> None:
        details = {}
        if vault_id:
            details["vault_id"] = vault_id
            message = f"Vault with ID '{vault_id}' not found"
        elif slug:
            details["slug"] = slug
            message = f"Vault with slug '{slug}' not found"
        else:
            message = "Vault not found"
        super().__init__(message, details)


class DuplicateVaultError(DomainException):
    """Vault with same slug already exists."""

    code = "DUPLICATE_VAULT"
    http_status = 409

    def __init__(self, slug: str) -> None:
        super().__init__(
            f"Vault with slug '{slug}' already exists",
            {"slug": slug},
        )


# Document Exceptions
class DocumentNotFoundError(DomainException):
    """Document does not exist."""

    code = "DOCUMENT_NOT_FOUND"
    http_status = 404

    def __init__(
        self, document_id: str | None = None, path: str | None = None
    ) -> None:
        details = {}
        if document_id:
            details["document_id"] = document_id
            message = f"Document with ID '{document_id}' not found"
        elif path:
            details["path"] = path
            message = f"Document at path '{path}' not found"
        else:
            message = "Document not found"
        super().__init__(message, details)


class DuplicateDocumentError(DomainException):
    """Document with same path already exists."""

    code = "DUPLICATE_DOCUMENT"
    http_status = 409

    def __init__(self, path: str) -> None:
        super().__init__(
            f"Document at path '{path}' already exists",
            {"path": path},
        )


# Folder Exceptions
class FolderNotFoundError(DomainException):
    """Folder does not exist."""

    code = "FOLDER_NOT_FOUND"
    http_status = 404

    def __init__(self, path: str) -> None:
        super().__init__(
            f"Folder at path '{path}' not found",
            {"path": path},
        )


# Parsing Exceptions
class InvalidFrontmatterError(DomainException):
    """Frontmatter YAML is invalid."""

    code = "INVALID_FRONTMATTER"
    http_status = 400

    def __init__(self, error: str) -> None:
        super().__init__(
            f"Invalid frontmatter YAML: {error}",
            {"parse_error": error},
        )


class InvalidWikiLinkError(DomainException):
    """Wiki-link syntax is invalid."""

    code = "INVALID_WIKI_LINK"
    http_status = 400

    def __init__(self, link_text: str, error: str) -> None:
        super().__init__(
            f"Invalid wiki-link '{link_text}': {error}",
            {"link_text": link_text, "parse_error": error},
        )


# Authentication Exceptions
class AuthenticationError(DomainException):
    """Authentication failed."""

    code = "UNAUTHORIZED"
    http_status = 401

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message)


class TokenExpiredError(DomainException):
    """JWT token has expired."""

    code = "TOKEN_EXPIRED"
    http_status = 401

    def __init__(self) -> None:
        super().__init__("Token has expired")


class InvalidCredentialsError(DomainException):
    """Invalid login credentials."""

    code = "INVALID_CREDENTIALS"
    http_status = 401

    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class UserNotFoundError(DomainException):
    """User does not exist."""

    code = "USER_NOT_FOUND"
    http_status = 404

    def __init__(self, user_id: str | None = None, email: str | None = None) -> None:
        if email:
            message = f"User with email '{email}' not found"
            details = {"email": email}
        elif user_id:
            message = f"User with ID '{user_id}' not found"
            details = {"user_id": user_id}
        else:
            message = "User not found"
            details = {}
        super().__init__(message, details)


class DuplicateUserError(DomainException):
    """User with same email already exists."""

    code = "DUPLICATE_USER"
    http_status = 409

    def __init__(self, email: str) -> None:
        super().__init__(
            f"User with email '{email}' already exists",
            {"email": email},
        )


# Authorization Exceptions
class ForbiddenError(DomainException):
    """Access denied to resource."""

    code = "FORBIDDEN"
    http_status = 403

    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(message)


# Service Exceptions
class EmbeddingServiceError(DomainException):
    """Embedding service unavailable or error."""

    code = "EMBEDDING_SERVICE_UNAVAILABLE"
    http_status = 503

    def __init__(self, error: str) -> None:
        super().__init__(
            f"Embedding service error: {error}",
            {"service_error": error},
        )


class GraphServiceError(DomainException):
    """Graph service error."""

    code = "GRAPH_SERVICE_ERROR"
    http_status = 500

    def __init__(self, error: str) -> None:
        super().__init__(
            f"Graph service error: {error}",
            {"service_error": error},
        )


# Table Exceptions
class TableNotFoundError(DomainException):
    """Table does not exist."""

    code = "TABLE_NOT_FOUND"
    http_status = 404

    def __init__(
        self, table_id: str | None = None, slug: str | None = None
    ) -> None:
        details = {}
        if table_id:
            details["table_id"] = table_id
            message = f"Table with ID '{table_id}' not found"
        elif slug:
            details["slug"] = slug
            message = f"Table with slug '{slug}' not found"
        else:
            message = "Table not found"
        super().__init__(message, details)


class DuplicateTableError(DomainException):
    """Table with same slug already exists."""

    code = "DUPLICATE_TABLE"
    http_status = 409

    def __init__(self, slug: str) -> None:
        super().__init__(
            f"Table with slug '{slug}' already exists",
            {"slug": slug},
        )


class RowNotFoundError(DomainException):
    """Row does not exist."""

    code = "ROW_NOT_FOUND"
    http_status = 404

    def __init__(self, row_id: str) -> None:
        super().__init__(
            f"Row with ID '{row_id}' not found",
            {"row_id": row_id},
        )


class SchemaValidationError(DomainException):
    """Row data does not conform to table schema."""

    code = "SCHEMA_VALIDATION_ERROR"
    http_status = 400

    def __init__(self, errors: list[str]) -> None:
        super().__init__(
            "Row data validation failed",
            {"validation_errors": errors},
        )


class ReferentialIntegrityError(DomainException):
    """Foreign key constraint violation."""

    code = "REFERENTIAL_INTEGRITY_ERROR"
    http_status = 400

    def __init__(
        self,
        message: str,
        source_table: str | None = None,
        target_table: str | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if source_table:
            details["source_table"] = source_table
        if target_table:
            details["target_table"] = target_table
        super().__init__(message, details)


class RelationshipNotFoundError(DomainException):
    """Relationship does not exist."""

    code = "RELATIONSHIP_NOT_FOUND"
    http_status = 404

    def __init__(self, relationship_id: str) -> None:
        super().__init__(
            f"Relationship with ID '{relationship_id}' not found",
            {"relationship_id": relationship_id},
        )


class DuplicateRelationshipError(DomainException):
    """Relationship already exists."""

    code = "DUPLICATE_RELATIONSHIP"
    http_status = 409

    def __init__(self, source_table: str, source_column: str) -> None:
        super().__init__(
            f"Relationship for column '{source_column}' in table '{source_table}' already exists",
            {"source_table": source_table, "source_column": source_column},
        )


class QueryParseError(DomainException):
    """Query syntax is invalid."""

    code = "QUERY_PARSE_ERROR"
    http_status = 400

    def __init__(self, query: str, error: str) -> None:
        super().__init__(
            f"Failed to parse query: {error}",
            {"query": query, "parse_error": error},
        )


class CsvParseError(DomainException):
    """CSV parsing failed."""

    code = "CSV_PARSE_ERROR"
    http_status = 400

    def __init__(self, error: str, line: int | None = None) -> None:
        details: dict[str, Any] = {"parse_error": error}
        if line is not None:
            details["line"] = line
        super().__init__(f"CSV parsing failed: {error}", details)
