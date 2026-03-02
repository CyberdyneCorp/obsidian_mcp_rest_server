"""Document use cases."""

from app.application.use_cases.document.create_document import CreateDocumentUseCase
from app.application.use_cases.document.delete_document import DeleteDocumentUseCase
from app.application.use_cases.document.get_document import GetDocumentUseCase
from app.application.use_cases.document.list_documents import ListDocumentsUseCase
from app.application.use_cases.document.update_document import UpdateDocumentUseCase

__all__ = [
    "CreateDocumentUseCase",
    "DeleteDocumentUseCase",
    "GetDocumentUseCase",
    "ListDocumentsUseCase",
    "UpdateDocumentUseCase",
]
