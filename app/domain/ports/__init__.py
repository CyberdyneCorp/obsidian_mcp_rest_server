"""Domain-level port interfaces.

These ports define the interfaces that domain services depend on.
They are implemented by infrastructure adapters and used via dependency injection.
"""

from app.domain.ports.repositories import (
    RelationshipRepositoryPort,
    RowRepositoryPort,
    TableRepositoryPort,
)

__all__ = [
    "RelationshipRepositoryPort",
    "RowRepositoryPort",
    "TableRepositoryPort",
]
