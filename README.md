# Obsidian Vault Server

MCP/REST server for Obsidian vault management with semantic search and knowledge graph capabilities.

## Features

- **Vault Ingestion**: Upload Obsidian vaults as ZIP files with full metadata preservation
- **Wiki-Link Support**: Full parsing of `[[wiki-links]]` with aliases, embeds, headers, and block references
- **Semantic Search**: Vector-based search using pgvector and OpenAI embeddings
- **Full-Text Search**: PostgreSQL full-text search with highlighting
- **Knowledge Graph**: Document connections via Apache AGE (Cypher queries)
- **Multi-User**: JWT authentication with user isolation
- **Hexagonal Architecture**: Clean separation of domain, application, and infrastructure layers

## Requirements

- Python 3.12+
- PostgreSQL 16 with pgvector and Apache AGE extensions
- OpenAI API key (for semantic search)

## Quick Start

### 1. Clone and Install

```bash
cd obsidian_vault_server

# Install dependencies (using uv)
just install-dev

# Or manually
uv sync --dev
```

### 2. Start Infrastructure

```bash
# Start PostgreSQL with pgvector + Apache AGE
just infra-up

# Or with docker-compose
docker-compose up -d
```

### 3. Configure Environment

Create a `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://obsidian:obsidian@localhost:5433/obsidian
OPENAI_API_KEY=your-openai-api-key
JWT_SECRET=your-secret-key-min-32-chars
```

### 4. Run Migrations

```bash
just migrate

# Or manually
uv run alembic upgrade head
```

### 5. Start Development Server

```bash
just dev

# Or manually
uv run uvicorn app.main:app --reload --port 8001
```

The server will be available at `http://localhost:8001`.

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get JWT tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user profile |

### Vaults

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/vaults` | List all vaults |
| POST | `/vaults` | Create vault |
| GET | `/vaults/{slug}` | Get vault |
| DELETE | `/vaults/{slug}` | Delete vault |
| POST | `/vaults/{slug}/ingest` | Upload ZIP |
| GET | `/vaults/{slug}/export` | Download ZIP |

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/vaults/{slug}/documents` | List documents |
| POST | `/vaults/{slug}/documents` | Create document |
| GET | `/vaults/{slug}/documents/{id}` | Get document |
| PATCH | `/vaults/{slug}/documents/{id}` | Update document |
| DELETE | `/vaults/{slug}/documents/{id}` | Delete document |

### Links

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/vaults/{slug}/documents/{id}/links/outgoing` | Get outgoing links |
| GET | `/vaults/{slug}/documents/{id}/links/incoming` | Get backlinks |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/vaults/{slug}/search/semantic` | Semantic search (requires embeddings) |
| GET | `/vaults/{slug}/search/fulltext` | Full-text search |

### Graph

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/vaults/{slug}/graph/connections/{id}` | Get document connections |
| GET | `/vaults/{slug}/graph/hubs` | Get most connected documents |
| GET | `/vaults/{slug}/graph/orphans` | Get documents with no connections |
| GET | `/vaults/{slug}/graph/path` | Get shortest path between documents |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection string (async) |
| `OPENAI_API_KEY` | - | OpenAI API key for embeddings (required for semantic search) |
| `JWT_SECRET` | `change-me-in-production` | Secret key for JWT tokens (change in production) |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token expiry in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token expiry in days |
| `EMBEDDING_MODEL` | `text-embedding-ada-002` | OpenAI embedding model |
| `EMBEDDING_DIMENSIONS` | `1536` | Embedding vector dimensions |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `DEBUG` | `False` | Enable debug mode |
| `STORAGE_PATH` | `./storage` | Path for file storage |
| `RATE_LIMIT_ENABLED` | `True` | Enable rate limiting |
| `CHUNK_SIZE` | `500` | Tokens per embedding chunk |
| `CHUNK_OVERLAP` | `50` | Token overlap between chunks |

## MCP Tools

The server exposes MCP tools for AI agent integration:

| Tool | Description |
|------|-------------|
| `list_vaults` | List all vaults |
| `get_document` | Get document by path or ID |
| `search_documents` | Semantic or fulltext search |
| `get_backlinks` | Get incoming links |
| `get_connections` | Get document graph |
| `list_documents` | List documents in vault |

## Development

```bash
# Run tests
just test

# Run tests with coverage
just test-cov

# Run linting
just lint

# Run type checking
just typecheck

# Format code
just format
```

## Architecture

The project follows **hexagonal architecture** (ports & adapters):

```
app/
├── domain/           # Pure Python - no external dependencies
│   ├── entities/     # Business objects (Vault, Document, Tag, etc.)
│   ├── value_objects/# Immutable values (WikiLink, Frontmatter, etc.)
│   ├── services/     # Domain logic (LinkResolver, TagParser, etc.)
│   └── exceptions.py # Domain exceptions
│
├── application/      # Use cases and ports
│   ├── interfaces/   # Port definitions (repositories, providers)
│   ├── use_cases/    # Application logic
│   └── dto/          # Data transfer objects
│
├── infrastructure/   # External adapters
│   ├── database/     # PostgreSQL repositories
│   ├── pgvector/     # Vector search adapter
│   ├── age/          # Apache AGE graph adapter
│   └── embedding/    # OpenAI embedding adapter
│
└── api/              # HTTP interface
    ├── routes/       # FastAPI endpoints
    └── schemas/      # Request/response models
```

## Database Schema

### Core Tables
- `users` - User accounts with JWT auth
- `vaults` - Obsidian vaults (per-user)
- `documents` - Markdown documents with metadata
- `folders` - Folder hierarchy
- `document_links` - Wiki-links between documents
- `tags` - Hierarchical tags
- `document_tags` - Document-tag associations

### Extensions
- `embedding_chunks` - pgvector embeddings for semantic search
- `obsidian_graph` - Apache AGE graph for relationship queries

## Testing

The project has comprehensive test coverage:

| Test Suite | Count |
|------------|-------|
| Unit Tests (Domain) | 77 |
| Unit Tests (Application) | 21 |
| BDD Scenarios | 27 |
| API Tests | 32 |
| Integration Tests | 27 |
| **Total** | **205** |

## License

MIT
