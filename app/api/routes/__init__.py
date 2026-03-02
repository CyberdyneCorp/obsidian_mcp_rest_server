"""API routes."""

from app.api.routes import auth, documents, graph, search, vaults

__all__ = ["auth", "vaults", "documents", "search", "graph"]
