"""Search use cases."""

from app.application.use_cases.search.semantic_search import SemanticSearchUseCase
from app.application.use_cases.search.fulltext_search import FulltextSearchUseCase

__all__ = [
    "FulltextSearchUseCase",
    "SemanticSearchUseCase",
]
