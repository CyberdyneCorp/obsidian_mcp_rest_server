"""FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exception_handlers import register_exception_handlers
from app.api.rate_limit import RateLimitMiddleware
from app.api.routes import auth, documents, graph, search, tables, vaults
from app.config import get_settings
from app.infrastructure.database.connection import close_db, init_db

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    _ = app
    logger.info("Starting Obsidian Vault Server...")
    await init_db()
    yield
    logger.info("Shutting down Obsidian Vault Server...")
    await close_db()


app = FastAPI(
    title="Obsidian Vault Server",
    description="MCP/REST server for Obsidian vault management with semantic search and knowledge graph",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials="*" not in settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.rate_limit_enabled:
    app.add_middleware(RateLimitMiddleware)

# Register exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(vaults.router, prefix="/vaults", tags=["Vaults"])
app.include_router(documents.router, tags=["Documents"])
app.include_router(tables.router, tags=["Tables"])
app.include_router(search.router, tags=["Search"])
app.include_router(graph.router, tags=["Graph"])

# Versioned aliases (`/v1`) for forward-compatible API evolution.
app.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
app.include_router(vaults.router, prefix="/v1/vaults", tags=["Vaults"])
app.include_router(documents.router, prefix="/v1", tags=["Documents"])
app.include_router(tables.router, prefix="/v1", tags=["Tables"])
app.include_router(search.router, prefix="/v1", tags=["Search"])
app.include_router(graph.router, prefix="/v1", tags=["Graph"])


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/", tags=["Root"])
async def root() -> dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "name": "Obsidian Vault Server",
        "version": "0.1.0",
        "docs": "/docs",
        "mcp": "/mcp",
        "api_versions": ["v1"],
        "default_api_base": "/v1",
    }
