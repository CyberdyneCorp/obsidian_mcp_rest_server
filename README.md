# Obsidian Vault Server

MCP/REST server for Obsidian vault management with semantic search, knowledge graph, and structured data capabilities.

## Features

### Core Capabilities
- **Vault Ingestion**: Upload Obsidian vaults as ZIP files with full metadata preservation
- **Wiki-Link Support**: Full parsing of `[[wiki-links]]` with aliases, embeds, headers, and block references
- **Semantic Search**: Vector-based search using pgvector and OpenAI embeddings
- **Full-Text Search**: PostgreSQL full-text search with highlighting
- **Knowledge Graph**: Document connections via Apache AGE (Cypher queries)
- **Multi-User**: JWT authentication with user isolation

### Structured Data
- **Tables**: User-defined tables with typed columns (text, number, boolean, date, JSON, arrays, references)
- **Row CRUD**: Full create, read, update, delete operations with filtering and pagination
- **Relationships**: Foreign keys between tables with CASCADE delete support
- **CSV Import/Export**: Bulk data operations with automatic type inference
- **Document-Table Links**: Documents can reference tables using `[[table:TableName]]` syntax
- **Query Language**: Dataview-compatible queries (`TABLE`, `WHERE`, `SORT`, `LIMIT`)

### Architecture
- **Hexagonal Architecture**: Clean separation of domain, application, and infrastructure layers
- **Dual Interface**: REST API and MCP (Model Context Protocol) for AI agent integration

```mermaid
graph TB
    subgraph "Clients"
        REST[REST API Clients]
        MCP[MCP/AI Agents]
    end

    subgraph "API Layer"
        FastAPI[FastAPI Routes]
        MCPTools[MCP Tools]
    end

    subgraph "Application Layer"
        UC[Use Cases]
        DTO[DTOs]
    end

    subgraph "Domain Layer"
        E[Entities]
        VO[Value Objects]
        DS[Domain Services]
    end

    subgraph "Infrastructure"
        PG[(PostgreSQL)]
        PGV[(pgvector)]
        AGE[(Apache AGE)]
        OAI[OpenAI API]
    end

    REST --> FastAPI
    MCP --> MCPTools
    FastAPI --> UC
    MCPTools --> UC
    UC --> E
    UC --> DS
    DS --> VO
    UC --> PG
    UC --> PGV
    UC --> AGE
    UC --> OAI
```

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

### Tables (Structured Data)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/vaults/{slug}/tables` | List all tables |
| POST | `/vaults/{slug}/tables` | Create table with schema |
| GET | `/vaults/{slug}/tables/{table}` | Get table schema |
| PATCH | `/vaults/{slug}/tables/{table}` | Update table |
| DELETE | `/vaults/{slug}/tables/{table}` | Delete table (cascades rows) |

### Table Rows

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/vaults/{slug}/tables/{table}/rows` | List rows (with filters) |
| POST | `/vaults/{slug}/tables/{table}/rows` | Create row |
| GET | `/vaults/{slug}/tables/{table}/rows/{id}` | Get row |
| PATCH | `/vaults/{slug}/tables/{table}/rows/{id}` | Update row |
| DELETE | `/vaults/{slug}/tables/{table}/rows/{id}` | Delete row |

### CSV Import/Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/vaults/{slug}/tables/import/csv` | Import CSV as new table |
| POST | `/vaults/{slug}/tables/{table}/import/csv` | Append CSV to table |
| GET | `/vaults/{slug}/tables/{table}/export/csv` | Export table as CSV |

### Document-Table Queries

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/vaults/{slug}/documents/{id}/tables` | Get tables referenced by document |
| GET | `/vaults/{slug}/tables/{table}/documents` | Get documents referencing table |
| POST | `/vaults/{slug}/documents/{id}/query` | Execute dataview-style query |

#### Row Filtering Query Parameters

```
?filter[column]=value          # Equality
?filter[column][gt]=value      # Greater than
?filter[column][lt]=value      # Less than
?filter[column][like]=pattern  # LIKE match
?sort=column&order=asc|desc    # Sorting
?limit=50&offset=0             # Pagination
?q=search_term                 # Full-text search
```

#### Dataview Query Syntax

```sql
TABLE name, email FROM Contacts WHERE status = 'active' SORT name ASC LIMIT 10
```

Supported clauses:
- `TABLE col1, col2 FROM table_name` - Select columns
- `WHERE column = value` - Filter (=, !=, >, <, LIKE, IN)
- `SORT column ASC|DESC` - Ordering
- `LIMIT n` - Limit results

## Structured Data Column Types

Tables support rich column types:

| Type | Description | Example |
|------|-------------|---------|
| `text` | String values | `"Hello World"` |
| `number` | Integer or float | `42`, `3.14` |
| `boolean` | True/False | `true` |
| `date` | Date only | `"2024-01-15"` |
| `datetime` | Date and time | `"2024-01-15T10:30:00Z"` |
| `json` | Nested objects | `{"key": "value"}` |
| `array` | List of values | `["a", "b", "c"]` |
| `reference` | FK to another table | `"uuid-of-row"` |
| `document` | Link to vault document | `"uuid-of-document"` |
| `computed` | Formula-based (stored) | `"=price * quantity"` |
| `richtext` | Markdown content | `"# Heading\n\nParagraph"` |

### Document-Table Link Syntax

Documents can reference tables using extended wiki-link syntax:

```markdown
# Project Notes

See all contacts: [[table:Contacts]]
Specific contact: [[row:Contacts/550e8400-e29b-41d4-a716-446655440000]]

## Embedded Query
```dataview
TABLE name, email FROM Contacts WHERE status = "active"
```
```

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

The server exposes MCP tools for AI agent integration via the Model Context Protocol.

```mermaid
graph LR
    subgraph "AI Agent"
        LLM[LLM]
    end

    subgraph "MCP Server"
        Tools[MCP Tools]
    end

    subgraph "Capabilities"
        Docs[Documents]
        Search[Search]
        Graph[Graph]
        Tables[Tables]
    end

    LLM <-->|MCP Protocol| Tools
    Tools --> Docs
    Tools --> Search
    Tools --> Graph
    Tools --> Tables
```

### Document Tools

| Tool | Description |
|------|-------------|
| `list_vaults` | List all vaults for the current user |
| `list_documents` | List documents in a vault with pagination |
| `get_document` | Get document content by path or ID |
| `get_backlinks` | Get incoming links to a document |

### Search Tools

| Tool | Description |
|------|-------------|
| `search_documents` | Semantic or full-text search across documents |

### Graph Tools

| Tool | Description |
|------|-------------|
| `get_connections` | Get connected documents within N hops |

### Structured Data Tools

| Tool | Description |
|------|-------------|
| `list_tables` | List all tables in a vault |
| `get_table` | Get table schema and column definitions |
| `list_table_rows` | List rows with filtering, sorting, and pagination |
| `get_table_row` | Get a specific row by ID |
| `query_table` | Execute dataview-style queries |

### MCP Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "obsidian-vault": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"],
      "env": {
        "DATABASE_URL": "postgresql+asyncpg://...",
        "JWT_SECRET": "your-secret"
      }
    }
  }
}
```

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

```mermaid
erDiagram
    users ||--o{ vaults : owns
    vaults ||--o{ documents : contains
    vaults ||--o{ folders : contains
    vaults ||--o{ tags : contains
    vaults ||--o{ data_tables : contains
    documents ||--o{ document_links : has
    documents ||--o{ document_tags : has
    documents ||--o{ embedding_chunks : has
    documents ||--o{ document_table_links : references
    data_tables ||--o{ table_rows : contains
    data_tables ||--o{ table_relationships : has
    data_tables ||--o{ document_table_links : referenced_by

    users {
        uuid id PK
        string email UK
        string password_hash
        string display_name
        boolean is_active
    }

    vaults {
        uuid id PK
        uuid user_id FK
        string name
        string slug UK
        int document_count
    }

    documents {
        uuid id PK
        uuid vault_id FK
        uuid folder_id FK
        string title
        string path
        text content
        jsonb frontmatter
    }

    data_tables {
        uuid id PK
        uuid vault_id FK
        string name
        string slug
        jsonb schema
        int row_count
    }

    table_rows {
        uuid id PK
        uuid table_id FK
        uuid vault_id FK
        jsonb data
    }
```

### Core Tables
- `users` - User accounts with JWT auth
- `vaults` - Obsidian vaults (per-user)
- `documents` - Markdown documents with metadata
- `folders` - Folder hierarchy
- `document_links` - Wiki-links between documents
- `tags` - Hierarchical tags
- `document_tags` - Document-tag associations

### Structured Data Tables
- `data_tables` - Table definitions with JSONB schema
- `table_rows` - Row data with JSONB storage (GIN indexed)
- `table_relationships` - Foreign key definitions between tables
- `document_table_links` - Links from documents to tables/rows

### Extensions
- `embedding_chunks` - pgvector embeddings for semantic search
- `obsidian_graph` - Apache AGE graph for relationship queries

## Testing

The project has comprehensive test coverage:

| Test Suite | Description |
|------------|-------------|
| Unit Tests (Domain) | Entity validation, value objects, domain services |
| Unit Tests (Application) | Use cases, DTOs, business logic |
| Unit Tests (Infrastructure) | Repositories, adapters, MCP tools |
| BDD Scenarios | Feature-driven tests with Gherkin syntax |
| API Tests | REST endpoint integration tests |
| Integration Tests | Full stack with database |

**Total: 433 tests**

```bash
# Run all tests
just test

# Run with coverage
just test-cov

# Run specific test suite
uv run pytest tests/unit -v
uv run pytest tests/api -v
uv run pytest tests/bdd -v
```

## License

MIT
