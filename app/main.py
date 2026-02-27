"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, documents, graph, search, vaults
from app.config import get_settings
from app.infrastructure.database.connection import init_db, close_db

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(vaults.router, prefix="/vaults", tags=["Vaults"])
app.include_router(documents.router, tags=["Documents"])
app.include_router(search.router, tags=["Search"])
app.include_router(graph.router, tags=["Graph"])


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "Obsidian Vault Server",
        "version": "0.1.0",
        "docs": "/docs",
        "mcp": "/mcp",
    }
