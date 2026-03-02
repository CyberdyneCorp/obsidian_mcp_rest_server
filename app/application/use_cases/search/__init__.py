"""Search use cases."""

from app.application.use_cases.search.fulltext_search import FulltextSearchUseCase
from app.application.use_cases.search.semantic_search import SemanticSearchUseCase

__all__ = [
    "FulltextSearchUseCase",
    "SemanticSearchUseCase",
]
