# Technical Requirements Document (TRD)

**Project:** Obsidian Vault MCP/REST Server
**Architecture:** Hexagonal (Ports & Adapters)
**Frameworks:** FastMCP + FastAPI
**Database:** PostgreSQL 16 (structured + pgvector + Apache AGE)
**Quality Standard:** BDD + TDD with ≥70% Test Coverage

---

# 1. Introduction

## 1.1 Purpose

This document defines the complete technical requirements for the Obsidian Vault MCP/REST Server. The system provides a centralized knowledge management platform that ingests Obsidian-style vaults, stores documents with full metadata preservation, and enables intelligent search and graph-based navigation.

## 1.2 Scope

The platform combines:

- **Vault Ingestion**: Upload Obsidian vaults as ZIP files with full structure preservation
- **Document Management**: CRUD operations on Markdown documents with frontmatter support
- **Wiki-Style Linking**: `[[Link]]` syntax parsing with bidirectional navigation
- **Semantic Search**: Vector-based search using pgvector and OpenAI embeddings
- **Knowledge Graph**: Document connections exposed via Apache AGE Cypher queries
- **Multi-User Authentication**: JWT-based auth with user isolation
- **MCP Tools**: AI-agent accessible tools via FastMCP (HTTP/SSE transport)
- **Vault Export**: Reconstruct and download vaults as ZIP files

## 1.3 Target Audience

- Backend developers implementing the system
- Frontend developers integrating with the API
- AI/ML engineers building agents that consume MCP tools
- DevOps engineers deploying and maintaining the infrastructure

## 1.4 Design Principles

The system follows these principles:

1. **Hexagonal Architecture**: Clean separation between domain, application, and infrastructure
2. **Domain-Driven Design**: Rich domain model with entities, value objects, and services
3. **Dependency Inversion**: Infrastructure depends on domain, never the reverse
4. **Test-First Development**: BDD scenarios and unit tests drive implementation
5. **Bridge Compatibility**: Schema and patterns aligned for future Bridge integration

---

# 2. High-Level Architecture

## 2.1 System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           External Systems                               │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │  AI Agents   │  │  Web Client  │  │    CLI       │  │   Bridge     ││
│  │  (MCP)       │  │  (REST)      │  │  (REST)      │  │  (Future)    ││
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘│
└─────────┼─────────────────┼─────────────────┼─────────────────┼────────┘
          │                 │                 │                 │
          │    MCP/SSE      │      REST       │      REST       │
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Obsidian Vault Server                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        API Layer                                   │  │
│  │  ┌─────────────────────┐  ┌─────────────────────────────────────┐│  │
│  │  │   FastMCP Server    │  │         FastAPI Routes              ││  │
│  │  │   (HTTP/SSE)        │  │   /auth  /vaults  /search  /graph   ││  │
│  │  └─────────────────────┘  └─────────────────────────────────────┘│  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                   │                                      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     Application Layer                              │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │  │
│  │  │ IngestVault │ │CreateDocument│ │SemanticSearch│ │GetConnections│ │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                   │                                      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                       Domain Layer                                 │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │  │
│  │  │    Vault    │ │  Document   │ │   Folder    │ │     Tag     │ │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                  │  │
│  │  │  WikiLink   │ │ Frontmatter │ │LinkResolver │                  │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                   │                                      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Infrastructure Layer                            │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │  │
│  │  │ PostgreSQL  │ │  pgvector   │ │ Apache AGE  │ │   OpenAI    │ │  │
│  │  │ Repositories│ │  Adapter    │ │  Adapter    │ │  Embeddings │ │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PostgreSQL 16                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │   Core DB    │  │   pgvector   │  │  Apache AGE  │                   │
│  │   Tables     │  │  Embeddings  │  │    Graph     │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Core Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| API Framework | FastAPI | REST endpoints, async support |
| MCP Server | FastMCP | AI-agent tool interface (HTTP/SSE) |
| Database | PostgreSQL 16 | Primary data store |
| Vector Store | pgvector | Semantic search embeddings |
| Graph Database | Apache AGE | Document relationship queries |
| Embeddings | OpenAI text-embedding-ada-002 | Vector generation |
| Authentication | JWT (HS256) | Multi-user auth |
| ORM | SQLAlchemy 2.x (async) | Database access |
| Migrations | Alembic | Schema management |

## 2.3 Development Tooling

| Tool | Purpose |
|------|---------|
| uv | Python package management |
| just | Task runner |
| pytest | Testing framework |
| pytest-bdd | BDD test support |
| pytest-cov | Coverage reporting |
| Ruff | Linting and formatting |
| Docker Compose | Local development |

---

# 3. System Capabilities

## 3.1 Vault Management

### 3.1.1 Create Vault

Users can create empty vaults to organize their knowledge:

- Provide name and optional description
- Auto-generate URL-safe slug
- Slug is unique per user (multi-user support)
- Initialize with empty folder structure

### 3.1.2 Ingest Vault (ZIP Upload)

Users can upload existing Obsidian vaults as ZIP files:

**Ingestion Process:**

1. **Extract ZIP**: Decompress to temporary directory
2. **Create Folder Hierarchy**: Mirror Obsidian folder structure
3. **Parse Documents**: For each `.md` file:
   - Extract YAML frontmatter (title, aliases, tags, custom fields)
   - Parse wiki-links `[[Target]]` and `[[Target|Display]]`
   - Extract inline tags `#tag` and `#tag/subtag`
   - Calculate content hash (SHA-256) for change detection
   - Count words and links
4. **Resolve Links**: Match wiki-links to target documents
   - Handle aliases and case-insensitive matching
   - Track unresolved links for later resolution
5. **Store Attachments**: Process images, PDFs, and other files
6. **Generate Embeddings**: Create vector embeddings (optional, background)
7. **Build Graph**: Create nodes and edges in Apache AGE

**Supported File Types:**

| Type | Extensions | Processing |
|------|------------|------------|
| Markdown | .md | Full parsing (frontmatter, links, tags) |
| Images | .png, .jpg, .jpeg, .gif, .svg, .webp | Store as attachments |
| PDFs | .pdf | Store as attachments |
| Other | * | Store as binary attachments |

### 3.1.3 Export Vault

Users can download their vault as a ZIP file:

1. Query all documents in vault
2. Reconstruct original folder structure
3. Generate Markdown files with frontmatter
4. Include attachments in original locations
5. Create and stream ZIP file

### 3.1.4 Sync Vault

After editing documents, users can trigger sync to:

- Recalculate content hashes
- Re-parse and resolve links
- Update backlink counts
- Regenerate embeddings for changed documents
- Update graph edges

---

## 3.2 Document Management

### 3.2.1 Document Structure

Each document contains:

| Field | Description |
|-------|-------------|
| title | Document title (from frontmatter or filename) |
| filename | Original filename (e.g., "My Note.md") |
| path | Full path within vault (e.g., "Projects/AI/My Note.md") |
| content | Markdown content (body only, frontmatter stored separately) |
| frontmatter | Parsed YAML as JSON object |
| aliases | Alternative names for linking |
| tags | Both frontmatter and inline tags |
| word_count | Word count in content |
| link_count | Number of outgoing wiki-links |
| backlink_count | Number of incoming wiki-links |
| created_at | Document creation time |
| updated_at | Last modification time |

### 3.2.2 CRUD Operations

**Create Document:**
- Provide path, content, optional frontmatter
- Auto-create parent folders
- Parse content for links and tags
- Generate embedding

**Read Document:**
- Get by ID or by path
- Include resolved links and backlinks
- Include tags and frontmatter

**Update Document:**
- Update content and/or frontmatter
- Re-parse links and tags
- Update content hash
- Regenerate embedding
- Update graph edges

**Delete Document:**
- Remove document and embedding chunks
- Update backlink counts on linking documents
- Remove graph nodes and edges

---

## 3.3 Wiki-Style Linking

### 3.3.1 Link Syntax

The system supports Obsidian-compatible wiki-link syntax:

| Pattern | Description |
|---------|-------------|
| `[[Target]]` | Link to document titled "Target" |
| `[[Target\|Display]]` | Link with custom display text |
| `[[Target#Heading]]` | Link to specific heading |
| `[[Target#^block-id]]` | Link to specific block |
| `![[Target]]` | Embed (transclude) document |
| `![[Image.png]]` | Embed image |

### 3.3.2 Link Resolution

Links are resolved using this priority:

1. **Exact title match** (case-insensitive)
2. **Alias match** (from frontmatter aliases)
3. **Filename match** (without extension)
4. **Path match** (relative or absolute)

Unresolved links are tracked with `is_resolved = false` and `target_document_id = NULL`.

### 3.3.3 Backlinks

Every document tracks incoming links (backlinks):

- Automatically maintained on document changes
- Query via dedicated endpoint
- Cached count in `backlink_count` field

---

## 3.4 Tag System

### 3.4.1 Tag Sources

Tags are extracted from two sources:

1. **Frontmatter**: YAML `tags` field (array or single value)
2. **Inline**: `#tag` and `#tag/subtag` patterns in content

### 3.4.2 Hierarchical Tags

Tags support hierarchy using `/` separator:

- `#projects` (root tag)
- `#projects/ai` (child tag)
- `#projects/ai/ml` (grandchild tag)

The system maintains the tag tree via `parent_tag_id` references.

### 3.4.3 Tag Operations

| Operation | Description |
|-----------|-------------|
| List vault tags | All tags with document counts |
| Get tag | Tag details with documents |
| Search by tag | Find documents with tag (including children) |
| Tag cloud | Popular tags by usage |

---

## 3.5 Semantic Search

### 3.5.1 Embedding Generation

Documents are chunked and embedded using OpenAI:

1. **Chunking**: Split document into ~500 token chunks with overlap
2. **Embedding**: Call OpenAI text-embedding-ada-002 (1536 dimensions)
3. **Storage**: Store vectors in pgvector with document reference

**Chunking Strategy:**
- Chunk size: 500 tokens
- Overlap: 50 tokens
- Preserve paragraph boundaries when possible

### 3.5.2 Search Flow

```
Query: "machine learning concepts"
    │
    ▼
┌─────────────────┐
│  Embed Query    │  (OpenAI API)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  pgvector       │  cosine similarity search
│  HNSW Index     │  on embedding_chunks
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Aggregate      │  group by document_id
│  Results        │  max(similarity) per doc
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Return         │  documents with scores
│  Documents      │
└─────────────────┘
```

### 3.5.3 Search Options

| Parameter | Description |
|-----------|-------------|
| query | Search query text |
| limit | Max results (default: 10) |
| threshold | Min similarity score (default: 0.7) |
| folder | Limit to folder path |
| tags | Filter by tags |

---

## 3.6 Graph Queries (Apache AGE)

### 3.6.1 Graph Schema

```cypher
-- Node label: Document
(:Document {
  id: uuid,
  title: string,
  path: string,
  vault_id: uuid
})

-- Edge label: LINKS_TO
(:Document)-[:LINKS_TO {
  type: string,      -- wikilink, embed, header, block
  display_text: string
}]->(:Document)
```

### 3.6.2 Graph Operations

| Operation | Description |
|-----------|-------------|
| Get Connections | All documents connected to a document (depth N) |
| Get Shortest Path | Shortest path between two documents |
| Get Clusters | Connected components in vault |
| Get Orphans | Documents with no links |
| Get Most Connected | Documents with most links |

### 3.6.3 Example Queries

**Get connections (2 hops):**
```cypher
MATCH (d:Document {id: $doc_id})-[*1..2]-(connected:Document)
WHERE d.vault_id = $vault_id
RETURN DISTINCT connected
```

**Get shortest path:**
```cypher
MATCH p = shortestPath(
  (a:Document {id: $source_id})-[*]-(b:Document {id: $target_id})
)
RETURN p
```

---

## 3.7 Full-Text Search

### 3.7.1 PostgreSQL FTS

Full-text search using PostgreSQL tsvector:

```sql
CREATE INDEX idx_documents_fts ON documents
USING gin(to_tsvector('english', content));
```

### 3.7.2 Search Syntax

| Pattern | Description |
|---------|-------------|
| `word` | Contains "word" |
| `word1 word2` | Contains both words |
| `word1 \| word2` | Contains either word |
| `"exact phrase"` | Contains exact phrase |
| `prefix*` | Prefix matching |

---

# 4. Backend Architecture (Hexagonal)

## 4.1 Layer Overview

```
┌─────────────────────────────────────────────────────────┐
│                     API Layer                            │
│   (FastAPI Routes, FastMCP Tools, Schemas)              │
│   Handles HTTP requests, validates input, returns JSON  │
└────────────────────────────┬────────────────────────────┘
                             │ depends on
                             ▼
┌─────────────────────────────────────────────────────────┐
│                 Application Layer                        │
│   (Use Cases, DTOs, Port Interfaces)                    │
│   Orchestrates domain objects, implements business flow │
└────────────────────────────┬────────────────────────────┘
                             │ depends on
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    Domain Layer                          │
│   (Entities, Value Objects, Domain Services)            │
│   Pure Python, no external dependencies, business rules │
└─────────────────────────────────────────────────────────┘
                             ▲
                             │ implements
┌─────────────────────────────────────────────────────────┐
│                Infrastructure Layer                      │
│   (Repositories, Adapters, Database Models)             │
│   Implements ports, handles persistence and external I/O│
└─────────────────────────────────────────────────────────┘
```

## 4.2 Domain Layer

### 4.2.1 Entities

**Vault (Aggregate Root)**
```python
class Vault:
    id: UUID
    user_id: UUID
    name: str
    slug: str
    description: str | None
    document_count: int
    created_at: datetime
    updated_at: datetime
```

**Document**
```python
class Document:
    id: UUID
    vault_id: UUID
    folder_id: UUID | None
    title: str
    filename: str
    path: str
    content: str
    content_hash: str
    frontmatter: Frontmatter
    aliases: list[str]
    word_count: int
    link_count: int
    backlink_count: int
    created_at: datetime
    updated_at: datetime
```

**Folder**
```python
class Folder:
    id: UUID
    vault_id: UUID
    parent_id: UUID | None
    name: str
    path: str
    depth: int
```

**Tag**
```python
class Tag:
    id: UUID
    vault_id: UUID
    name: str
    slug: str
    parent_tag_id: UUID | None
    document_count: int
```

**DocumentLink**
```python
class DocumentLink:
    id: UUID
    vault_id: UUID
    source_document_id: UUID
    target_document_id: UUID | None
    link_text: str
    display_text: str | None
    link_type: LinkType  # wikilink, embed, header, block
    is_resolved: bool
    position_start: int
```

### 4.2.2 Value Objects

**WikiLink**
```python
@dataclass(frozen=True)
class WikiLink:
    target: str           # "Target Document"
    display_text: str     # "Display" or same as target
    heading: str | None   # "#Heading"
    block_id: str | None  # "^block-id"
    is_embed: bool        # starts with !

    @classmethod
    def parse(cls, text: str) -> WikiLink: ...
```

**Frontmatter**
```python
@dataclass(frozen=True)
class Frontmatter:
    title: str | None
    aliases: list[str]
    tags: list[str]
    custom_fields: dict[str, Any]

    @classmethod
    def parse(cls, yaml_text: str) -> Frontmatter: ...

    def to_yaml(self) -> str: ...
```

**DocumentPath**
```python
@dataclass(frozen=True)
class DocumentPath:
    path: str  # "Projects/AI/My Note.md"

    @property
    def folder_path(self) -> str: ...  # "Projects/AI"

    @property
    def filename(self) -> str: ...  # "My Note.md"

    @property
    def title(self) -> str: ...  # "My Note"
```

### 4.2.3 Domain Services

**LinkResolver**
```python
class LinkResolver:
    def resolve(
        self,
        link: WikiLink,
        documents: list[Document]
    ) -> Document | None:
        """Resolve wiki-link to target document."""
```

**TagParser**
```python
class TagParser:
    def extract_inline_tags(self, content: str) -> list[str]:
        """Extract #tags from content."""

    def parse_hierarchical_tag(self, tag: str) -> list[str]:
        """Split #tag/subtag into hierarchy."""
```

**MarkdownProcessor**
```python
class MarkdownProcessor:
    def extract_frontmatter(self, content: str) -> tuple[Frontmatter, str]:
        """Separate frontmatter from content."""

    def extract_links(self, content: str) -> list[WikiLink]:
        """Extract all wiki-links from content."""

    def count_words(self, content: str) -> int:
        """Count words in markdown content."""
```

### 4.2.4 Domain Exceptions

```python
class DomainException(Exception):
    """Base domain exception."""

class VaultNotFoundError(DomainException):
    """Vault does not exist."""

class DocumentNotFoundError(DomainException):
    """Document does not exist."""

class DuplicateDocumentError(DomainException):
    """Document with same path already exists."""

class InvalidFrontmatterError(DomainException):
    """Frontmatter YAML is invalid."""

class InvalidWikiLinkError(DomainException):
    """Wiki-link syntax is invalid."""
```

## 4.3 Application Layer

### 4.3.1 Port Interfaces

**Repository Ports**
```python
class VaultRepository(Protocol):
    async def get_by_id(self, vault_id: UUID) -> Vault | None: ...
    async def get_by_slug(self, user_id: UUID, slug: str) -> Vault | None: ...
    async def create(self, vault: Vault) -> Vault: ...
    async def update(self, vault: Vault) -> Vault: ...
    async def delete(self, vault_id: UUID) -> None: ...
    async def list_by_user(self, user_id: UUID) -> list[Vault]: ...

class DocumentRepository(Protocol):
    async def get_by_id(self, doc_id: UUID) -> Document | None: ...
    async def get_by_path(self, vault_id: UUID, path: str) -> Document | None: ...
    async def create(self, document: Document) -> Document: ...
    async def update(self, document: Document) -> Document: ...
    async def delete(self, doc_id: UUID) -> None: ...
    async def list_by_vault(self, vault_id: UUID) -> list[Document]: ...
    async def list_by_folder(self, folder_id: UUID) -> list[Document]: ...
    async def search_fulltext(self, vault_id: UUID, query: str) -> list[Document]: ...
```

**Embedding Provider Port**
```python
class EmbeddingProvider(Protocol):
    async def embed_text(self, text: str) -> list[float]: ...
    async def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
```

**Graph Provider Port**
```python
class GraphProvider(Protocol):
    async def create_document_node(self, document: Document) -> None: ...
    async def delete_document_node(self, doc_id: UUID) -> None: ...
    async def create_link_edge(self, source_id: UUID, target_id: UUID, link_type: str) -> None: ...
    async def delete_link_edge(self, source_id: UUID, target_id: UUID) -> None: ...
    async def get_connections(self, doc_id: UUID, depth: int) -> list[Document]: ...
    async def get_shortest_path(self, source_id: UUID, target_id: UUID) -> list[Document]: ...
```

**Storage Port**
```python
class StorageProvider(Protocol):
    async def save_attachment(self, vault_id: UUID, path: str, content: bytes) -> str: ...
    async def get_attachment(self, vault_id: UUID, path: str) -> bytes: ...
    async def delete_attachment(self, vault_id: UUID, path: str) -> None: ...
```

### 4.3.2 Use Cases

**IngestVaultUseCase**
```python
class IngestVaultUseCase:
    def __init__(
        self,
        vault_repo: VaultRepository,
        document_repo: DocumentRepository,
        folder_repo: FolderRepository,
        link_repo: DocumentLinkRepository,
        tag_repo: TagRepository,
        embedding_provider: EmbeddingProvider,
        graph_provider: GraphProvider,
    ): ...

    async def execute(
        self,
        user_id: UUID,
        vault_name: str,
        zip_content: bytes,
        generate_embeddings: bool = True,
    ) -> Vault: ...
```

**SemanticSearchUseCase**
```python
class SemanticSearchUseCase:
    def __init__(
        self,
        document_repo: DocumentRepository,
        embedding_repo: EmbeddingChunkRepository,
        embedding_provider: EmbeddingProvider,
    ): ...

    async def execute(
        self,
        vault_id: UUID,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
        folder_path: str | None = None,
        tags: list[str] | None = None,
    ) -> list[SearchResult]: ...
```

**GetBacklinksUseCase**
```python
class GetBacklinksUseCase:
    def __init__(
        self,
        document_repo: DocumentRepository,
        link_repo: DocumentLinkRepository,
    ): ...

    async def execute(
        self,
        document_id: UUID,
    ) -> list[DocumentWithLink]: ...
```

### 4.3.3 DTOs

```python
@dataclass
class VaultDTO:
    id: UUID
    name: str
    slug: str
    description: str | None
    document_count: int
    created_at: datetime
    updated_at: datetime

@dataclass
class DocumentDTO:
    id: UUID
    title: str
    path: str
    content: str
    frontmatter: dict
    tags: list[str]
    word_count: int
    link_count: int
    backlink_count: int
    created_at: datetime
    updated_at: datetime

@dataclass
class SearchResultDTO:
    document: DocumentDTO
    score: float
    matched_chunk: str
```

## 4.4 Infrastructure Layer

### 4.4.1 Database Models (SQLAlchemy)

```python
class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_login_at: Mapped[datetime | None]

class VaultModel(Base):
    __tablename__ = "vaults"
    __table_args__ = (UniqueConstraint("user_id", "slug"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    document_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(onupdate=datetime.utcnow)

class DocumentModel(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("vault_id", "path"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    vault_id: Mapped[UUID] = mapped_column(ForeignKey("vaults.id"))
    folder_id: Mapped[UUID | None] = mapped_column(ForeignKey("folders.id"))
    title: Mapped[str] = mapped_column(String(500))
    filename: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    frontmatter: Mapped[dict] = mapped_column(JSONB, default={})
    aliases: Mapped[list] = mapped_column(ARRAY(Text), default=[])
    word_count: Mapped[int] = mapped_column(default=0)
    link_count: Mapped[int] = mapped_column(default=0)
    backlink_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(onupdate=datetime.utcnow)
```

### 4.4.2 Repository Implementations

```python
class PostgresVaultRepository:
    def __init__(self, session: AsyncSession): ...

    async def get_by_id(self, vault_id: UUID) -> Vault | None:
        stmt = select(VaultModel).where(VaultModel.id == vault_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    def _to_entity(self, model: VaultModel) -> Vault:
        return Vault(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            # ... mapping
        )
```

### 4.4.3 pgvector Adapter

```python
class PgvectorEmbeddingRepository:
    async def search_similar(
        self,
        vault_id: UUID,
        embedding: list[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> list[EmbeddingChunkWithScore]:
        stmt = (
            select(
                EmbeddingChunkModel,
                EmbeddingChunkModel.embedding.cosine_distance(embedding).label("distance")
            )
            .where(EmbeddingChunkModel.vault_id == vault_id)
            .where(1 - EmbeddingChunkModel.embedding.cosine_distance(embedding) >= threshold)
            .order_by("distance")
            .limit(limit)
        )
        # ...
```

### 4.4.4 Apache AGE Adapter

```python
class AgeGraphAdapter:
    async def get_connections(
        self,
        doc_id: UUID,
        vault_id: UUID,
        depth: int = 2,
    ) -> list[Document]:
        query = """
        SELECT * FROM cypher('obsidian_graph', $$
            MATCH (d:Document {id: $doc_id})-[*1..$depth]-(connected:Document)
            WHERE d.vault_id = $vault_id
            RETURN DISTINCT connected
        $$) as (connected agtype);
        """
        # ...
```

### 4.4.5 OpenAI Embedding Adapter

```python
class OpenAIEmbeddingAdapter:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def embed_text(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model="text-embedding-ada-002",
            input=text,
        )
        return response.data[0].embedding

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(
            model="text-embedding-ada-002",
            input=texts,
        )
        return [d.embedding for d in response.data]
```

## 4.5 API Layer

### 4.5.1 FastAPI Application Structure

```python
# app/main.py
from fastapi import FastAPI
from app.api.routes import auth, vaults, documents, search, graph

app = FastAPI(title="Obsidian Vault Server")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(vaults.router, prefix="/vaults", tags=["vaults"])
app.include_router(documents.router, tags=["documents"])
app.include_router(search.router, tags=["search"])
app.include_router(graph.router, tags=["graph"])
```

### 4.5.2 Dependency Injection

```python
# app/api/dependencies.py
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    # Validate JWT and return user
    ...

def get_vault_repository(
    session: AsyncSession = Depends(get_db_session),
) -> VaultRepository:
    return PostgresVaultRepository(session)
```

---

# 5. API Endpoints Specification

## 5.1 Authentication

### POST /auth/register

Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "display_name": "John Doe"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "John Doe",
  "created_at": "2025-01-01T00:00:00Z"
}
```

### POST /auth/login

Authenticate and receive JWT tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST /auth/refresh

Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### GET /auth/me

Get current user profile.

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "John Doe",
  "created_at": "2025-01-01T00:00:00Z",
  "last_login_at": "2025-01-15T10:30:00Z"
}
```

---

## 5.2 Vaults

### GET /vaults

List all vaults for current user.

**Response (200):**
```json
{
  "vaults": [
    {
      "id": "uuid",
      "name": "Personal Notes",
      "slug": "personal-notes",
      "description": "My personal knowledge base",
      "document_count": 150,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

### POST /vaults

Create a new vault.

**Request:**
```json
{
  "name": "Personal Notes",
  "description": "My personal knowledge base"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "name": "Personal Notes",
  "slug": "personal-notes",
  "description": "My personal knowledge base",
  "document_count": 0,
  "created_at": "2025-01-01T00:00:00Z"
}
```

### GET /vaults/{slug}

Get vault details.

### POST /vaults/{slug}/ingest

Upload and ingest a ZIP file.

**Request:** `multipart/form-data`
- `file`: ZIP file
- `generate_embeddings`: boolean (optional, default: true)

**Response (202):**
```json
{
  "vault_id": "uuid",
  "status": "processing",
  "documents_found": 150,
  "message": "Vault ingestion started"
}
```

### GET /vaults/{slug}/export

Export vault as ZIP file.

**Response:** `application/zip` stream

### DELETE /vaults/{slug}

Delete vault and all contents.

---

## 5.3 Documents

### GET /vaults/{slug}/documents

List documents in vault.

**Query Parameters:**
- `folder`: Filter by folder path
- `tag`: Filter by tag
- `limit`: Max results (default: 50)
- `offset`: Pagination offset

**Response (200):**
```json
{
  "documents": [
    {
      "id": "uuid",
      "title": "Machine Learning Basics",
      "path": "AI/Machine Learning Basics.md",
      "word_count": 1500,
      "link_count": 5,
      "backlink_count": 3,
      "tags": ["#ai", "#ml"],
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### GET /vaults/{slug}/documents/{id}

Get document by ID.

**Response (200):**
```json
{
  "id": "uuid",
  "title": "Machine Learning Basics",
  "path": "AI/Machine Learning Basics.md",
  "content": "# Machine Learning Basics\n\n...",
  "frontmatter": {
    "title": "Machine Learning Basics",
    "aliases": ["ML Basics"],
    "tags": ["ai", "ml"]
  },
  "tags": ["#ai", "#ml"],
  "word_count": 1500,
  "link_count": 5,
  "backlink_count": 3,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### POST /vaults/{slug}/documents

Create a new document.

**Request:**
```json
{
  "path": "AI/New Document.md",
  "content": "# New Document\n\nContent here...",
  "frontmatter": {
    "tags": ["ai"]
  }
}
```

### PATCH /vaults/{slug}/documents/{id}

Update document.

**Request:**
```json
{
  "content": "# Updated Content\n\n...",
  "frontmatter": {
    "tags": ["ai", "updated"]
  }
}
```

### DELETE /vaults/{slug}/documents/{id}

Delete document.

### GET /vaults/{slug}/documents/{id}/links/outgoing

Get outgoing links from document.

**Response (200):**
```json
{
  "links": [
    {
      "id": "uuid",
      "link_text": "Related Topic",
      "display_text": "Related Topic",
      "link_type": "wikilink",
      "is_resolved": true,
      "target_document": {
        "id": "uuid",
        "title": "Related Topic",
        "path": "Topics/Related Topic.md"
      }
    }
  ]
}
```

### GET /vaults/{slug}/documents/{id}/links/incoming

Get backlinks (incoming links) to document.

**Response (200):**
```json
{
  "backlinks": [
    {
      "document": {
        "id": "uuid",
        "title": "Linking Document",
        "path": "Notes/Linking Document.md"
      },
      "link_text": "Machine Learning Basics",
      "context": "...as described in [[Machine Learning Basics]]..."
    }
  ]
}
```

---

## 5.4 Search

### POST /vaults/{slug}/search/semantic

Semantic (vector) search.

**Request:**
```json
{
  "query": "machine learning concepts",
  "limit": 10,
  "threshold": 0.7,
  "folder": "AI",
  "tags": ["#ml"]
}
```

**Response (200):**
```json
{
  "results": [
    {
      "document": {
        "id": "uuid",
        "title": "Machine Learning Basics",
        "path": "AI/Machine Learning Basics.md"
      },
      "score": 0.92,
      "matched_chunk": "Machine learning is a subset of artificial intelligence..."
    }
  ],
  "query": "machine learning concepts",
  "total": 5
}
```

### GET /vaults/{slug}/search/fulltext

Full-text search.

**Query Parameters:**
- `q`: Search query
- `limit`: Max results
- `folder`: Filter by folder

**Response (200):**
```json
{
  "results": [
    {
      "document": {
        "id": "uuid",
        "title": "Machine Learning Basics",
        "path": "AI/Machine Learning Basics.md"
      },
      "headline": "...introduces <mark>machine</mark> <mark>learning</mark> concepts..."
    }
  ]
}
```

---

## 5.5 Graph

### GET /vaults/{slug}/graph/connections/{document_id}

Get connected documents.

**Query Parameters:**
- `depth`: Traversal depth (default: 2, max: 5)

**Response (200):**
```json
{
  "center": {
    "id": "uuid",
    "title": "Machine Learning Basics",
    "path": "AI/Machine Learning Basics.md"
  },
  "connections": [
    {
      "document": {
        "id": "uuid",
        "title": "Neural Networks",
        "path": "AI/Neural Networks.md"
      },
      "distance": 1,
      "link_type": "outgoing"
    }
  ]
}
```

### GET /vaults/{slug}/graph/path

Get shortest path between documents.

**Query Parameters:**
- `source`: Source document ID
- `target`: Target document ID

**Response (200):**
```json
{
  "path": [
    {"id": "uuid1", "title": "Doc A"},
    {"id": "uuid2", "title": "Doc B"},
    {"id": "uuid3", "title": "Doc C"}
  ],
  "length": 2
}
```

### GET /vaults/{slug}/graph/orphans

Get documents with no links.

### GET /vaults/{slug}/graph/hubs

Get most connected documents.

---

# 6. Error Handling Strategy

## 6.1 Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VAULT_NOT_FOUND",
    "message": "Vault with slug 'test-vault' not found",
    "details": {
      "slug": "test-vault"
    }
  }
}
```

## 6.2 Error Codes

| HTTP | Code | Description |
|------|------|-------------|
| 400 | INVALID_REQUEST | Request validation failed |
| 400 | INVALID_FRONTMATTER | Frontmatter YAML is malformed |
| 400 | INVALID_WIKI_LINK | Wiki-link syntax is invalid |
| 401 | UNAUTHORIZED | Authentication required |
| 401 | TOKEN_EXPIRED | JWT token has expired |
| 403 | FORBIDDEN | Access denied to resource |
| 404 | VAULT_NOT_FOUND | Vault does not exist |
| 404 | DOCUMENT_NOT_FOUND | Document does not exist |
| 404 | FOLDER_NOT_FOUND | Folder does not exist |
| 409 | DUPLICATE_VAULT | Vault slug already exists |
| 409 | DUPLICATE_DOCUMENT | Document path already exists |
| 422 | UNPROCESSABLE_ENTITY | Semantic validation failed |
| 500 | INTERNAL_ERROR | Unexpected server error |
| 503 | EMBEDDING_SERVICE_UNAVAILABLE | OpenAI API unavailable |

## 6.3 Exception Handling

```python
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=exc.http_status,
        content={"error": {"code": exc.code, "message": str(exc)}},
    )
```

---

# 7. Database Design

## 7.1 Entity Relationship Diagram

```
┌──────────────┐
│    users     │
├──────────────┤
│ id (PK)      │
│ email        │
│ password_hash│
│ display_name │
│ is_active    │
│ created_at   │
│ last_login_at│
└──────┬───────┘
       │
       │ 1:N
       ▼
┌──────────────┐       ┌──────────────┐
│    vaults    │       │   folders    │
├──────────────┤       ├──────────────┤
│ id (PK)      │◄──────│ vault_id (FK)│
│ user_id (FK) │       │ id (PK)      │
│ name         │       │ parent_id(FK)│
│ slug         │       │ name         │
│ description  │       │ path         │
│ document_cnt │       │ depth        │
└──────┬───────┘       └──────┬───────┘
       │                      │
       │ 1:N                  │ 1:N
       ▼                      ▼
┌─────────────────────────────────────────┐
│              documents                   │
├─────────────────────────────────────────┤
│ id (PK)                                  │
│ vault_id (FK)                            │
│ folder_id (FK)                           │
│ title, filename, path, content           │
│ content_hash, frontmatter, aliases       │
│ word_count, link_count, backlink_count   │
│ created_at, updated_at                   │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┼─────────┬─────────────────┐
    │         │         │                 │
    ▼         ▼         ▼                 ▼
┌────────┐ ┌────────┐ ┌──────────────┐ ┌────────────────┐
│ links  │ │doc_tags│ │   chunks     │ │      tags      │
├────────┤ ├────────┤ ├──────────────┤ ├────────────────┤
│ id     │ │doc_id  │ │ id           │ │ id (PK)        │
│vault_id│ │tag_id  │ │ vault_id     │ │ vault_id (FK)  │
│src_doc │ │ source │ │ document_id  │ │ name           │
│tgt_doc │ └────────┘ │ chunk_index  │ │ slug           │
│link_txt│            │ content      │ │ parent_tag_id  │
│disp_txt│            │ token_count  │ │ document_count │
│type    │            │ embedding    │ └────────────────┘
│resolved│            └──────────────┘
│pos_strt│
└────────┘
```

## 7.2 Table Definitions

### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);
```

### vaults
```sql
CREATE TABLE vaults (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    document_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, slug)
);

CREATE INDEX idx_vaults_user_id ON vaults(user_id);
CREATE INDEX idx_vaults_slug ON vaults(user_id, slug);
```

### folders
```sql
CREATE TABLE folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vault_id UUID NOT NULL REFERENCES vaults(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,
    depth INTEGER NOT NULL DEFAULT 0,

    UNIQUE(vault_id, path)
);

CREATE INDEX idx_folders_vault_id ON folders(vault_id);
CREATE INDEX idx_folders_parent_id ON folders(parent_id);
CREATE INDEX idx_folders_path ON folders(vault_id, path);
```

### documents
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vault_id UUID NOT NULL REFERENCES vaults(id) ON DELETE CASCADE,
    folder_id UUID REFERENCES folders(id) ON DELETE SET NULL,
    title VARCHAR(500) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    content_hash VARCHAR(64) NOT NULL,
    frontmatter JSONB DEFAULT '{}',
    aliases TEXT[] DEFAULT '{}',
    word_count INTEGER DEFAULT 0,
    link_count INTEGER DEFAULT 0,
    backlink_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(vault_id, path)
);

CREATE INDEX idx_documents_vault_id ON documents(vault_id);
CREATE INDEX idx_documents_folder_id ON documents(folder_id);
CREATE INDEX idx_documents_path ON documents(vault_id, path);
CREATE INDEX idx_documents_title ON documents(vault_id, title);
CREATE INDEX idx_documents_fts ON documents USING gin(to_tsvector('english', content));
CREATE INDEX idx_documents_frontmatter ON documents USING gin(frontmatter);
CREATE INDEX idx_documents_aliases ON documents USING gin(aliases);
```

### document_links
```sql
CREATE TABLE document_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vault_id UUID NOT NULL REFERENCES vaults(id) ON DELETE CASCADE,
    source_document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    target_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    link_text VARCHAR(500) NOT NULL,
    display_text VARCHAR(500),
    link_type VARCHAR(20) NOT NULL DEFAULT 'wikilink',
    is_resolved BOOLEAN DEFAULT FALSE,
    position_start INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_links_vault_id ON document_links(vault_id);
CREATE INDEX idx_links_source ON document_links(source_document_id);
CREATE INDEX idx_links_target ON document_links(target_document_id);
CREATE INDEX idx_links_unresolved ON document_links(vault_id) WHERE NOT is_resolved;
```

### tags
```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vault_id UUID NOT NULL REFERENCES vaults(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    parent_tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    document_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(vault_id, slug)
);

CREATE INDEX idx_tags_vault_id ON tags(vault_id);
CREATE INDEX idx_tags_parent ON tags(parent_tag_id);
CREATE INDEX idx_tags_name ON tags(vault_id, name);
```

### document_tags
```sql
CREATE TABLE document_tags (
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    source VARCHAR(20) NOT NULL DEFAULT 'inline',

    PRIMARY KEY(document_id, tag_id)
);

CREATE INDEX idx_document_tags_document ON document_tags(document_id);
CREATE INDEX idx_document_tags_tag ON document_tags(tag_id);
```

### embedding_chunks (pgvector)
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embedding_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vault_id UUID NOT NULL REFERENCES vaults(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    embedding vector(1536) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(document_id, chunk_index)
);

CREATE INDEX idx_chunks_vault_id ON embedding_chunks(vault_id);
CREATE INDEX idx_chunks_document_id ON embedding_chunks(document_id);
CREATE INDEX idx_chunks_embedding ON embedding_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

### Apache AGE Graph Setup
```sql
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';

SET search_path = ag_catalog, "$user", public;

SELECT create_graph('obsidian_graph');

-- Nodes and edges are created via Cypher queries
```

---

# 8. MCP Server Specification

## 8.1 Transport

- **Protocol**: HTTP with Server-Sent Events (SSE)
- **Base URL**: `http://localhost:8000/mcp`
- **Authentication**: Bearer JWT token

## 8.2 Tools

### list_vaults

List all vaults for the authenticated user.

**Parameters:** None

**Returns:**
```json
{
  "vaults": [
    {
      "id": "uuid",
      "name": "Personal Notes",
      "slug": "personal-notes",
      "document_count": 150
    }
  ]
}
```

### get_document

Get a document by path or ID.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| vault_slug | string | Yes | Vault slug |
| path | string | No | Document path |
| document_id | string | No | Document UUID |

**Returns:**
```json
{
  "id": "uuid",
  "title": "Machine Learning Basics",
  "path": "AI/Machine Learning Basics.md",
  "content": "# Machine Learning...",
  "frontmatter": {...},
  "tags": ["#ai", "#ml"]
}
```

### search_documents

Search documents using semantic or full-text search.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| vault_slug | string | Yes | Vault slug |
| query | string | Yes | Search query |
| search_type | string | No | "semantic" or "fulltext" (default: semantic) |
| limit | integer | No | Max results (default: 10) |
| folder | string | No | Filter by folder |
| tags | array | No | Filter by tags |

### get_backlinks

Get documents that link to a specific document.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| vault_slug | string | Yes | Vault slug |
| document_id | string | Yes | Document UUID |

### get_connections

Get the document graph around a document.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| vault_slug | string | Yes | Vault slug |
| document_id | string | Yes | Document UUID |
| depth | integer | No | Traversal depth (default: 2) |

### create_document

Create a new document.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| vault_slug | string | Yes | Vault slug |
| path | string | Yes | Document path |
| content | string | Yes | Markdown content |
| frontmatter | object | No | Frontmatter fields |

### update_document

Update an existing document.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| vault_slug | string | Yes | Vault slug |
| document_id | string | Yes | Document UUID |
| content | string | No | New content |
| frontmatter | object | No | Updated frontmatter |

## 8.3 MCP Server Implementation

```python
# app/mcp_server.py
from fastmcp import FastMCP

mcp = FastMCP("Obsidian Vault Server")

@mcp.tool()
async def list_vaults(ctx: Context) -> list[dict]:
    """List all vaults for the current user."""
    user = get_user_from_context(ctx)
    use_case = ctx.deps.list_vaults_use_case
    return await use_case.execute(user.id)

@mcp.tool()
async def search_documents(
    ctx: Context,
    vault_slug: str,
    query: str,
    search_type: str = "semantic",
    limit: int = 10,
) -> list[dict]:
    """Search documents using semantic or full-text search."""
    # Implementation
```

---

# 9. Security

## 9.1 Authentication

### JWT Configuration

| Setting | Value |
|---------|-------|
| Algorithm | HS256 |
| Access Token Expiry | 1 hour |
| Refresh Token Expiry | 7 days |
| Issuer | obsidian-vault-server |

### Password Hashing

- **Algorithm**: Argon2id
- **Time Cost**: 3
- **Memory Cost**: 65536 KB
- **Parallelism**: 4

## 9.2 Authorization

All vault operations require:
1. Valid JWT token
2. User owns the vault (user_id match)

MCP tools extract user from context (JWT passed via headers).

## 9.3 Input Validation

- All inputs validated via Pydantic schemas
- File uploads limited to 100MB
- Path traversal prevention
- SQL injection prevented via parameterized queries
- XSS prevention via proper escaping

## 9.4 Rate Limiting

| Endpoint | Limit |
|----------|-------|
| /auth/login | 5/minute |
| /auth/register | 3/minute |
| /vaults/{slug}/ingest | 2/hour |
| Search endpoints | 30/minute |
| Other endpoints | 100/minute |

---

# 10. Testing Requirements

## 10.1 BDD Scenarios (pytest-bdd)

### Feature: Vault Ingestion

```gherkin
Feature: Vault Ingestion
  As a user
  I want to upload my Obsidian vault
  So that I can search and navigate my notes

  Background:
    Given I am an authenticated user
    And I have created a vault "test-vault"

  Scenario: Ingest vault from ZIP file
    Given I have a ZIP file containing:
      | path                    | content                           |
      | Notes/First Note.md     | # First Note\n\nSome content      |
      | Notes/Second Note.md    | # Second Note\n\n[[First Note]]   |
    When I upload the ZIP to "/vaults/test-vault/ingest"
    Then the response status should be 202
    And the vault should contain 2 documents
    And "Second Note" should have a link to "First Note"

  Scenario: Parse wiki-links from document
    Given a document with content:
      """
      # My Note

      This links to [[Target Document]].
      Also links to [[Another|Custom Display]].
      And embeds ![[Embedded Note]].
      """
    When the document is parsed
    Then 3 wiki-links should be extracted
    And the links should include:
      | target          | display         | is_embed |
      | Target Document | Target Document | false    |
      | Another         | Custom Display  | false    |
      | Embedded Note   | Embedded Note   | true     |

  Scenario: Resolve links to target documents
    Given documents exist:
      | path           | aliases        |
      | Notes/Doc A.md | ["A", "DocA"]  |
      | Notes/Doc B.md | []             |
    And a link with text "A"
    When the link is resolved
    Then the target should be "Notes/Doc A.md"

  Scenario: Handle unresolved links
    Given documents exist:
      | path           |
      | Notes/Doc A.md |
    And a link with text "Nonexistent"
    When the link is resolved
    Then the link should be marked as unresolved
```

### Feature: Document Linking

```gherkin
Feature: Document Linking
  As a user
  I want to navigate between linked documents
  So that I can explore my knowledge graph

  Scenario: Get outgoing links from document
    Given a document "Source.md" with links to:
      | target          |
      | Target A        |
      | Target B        |
    When I request outgoing links for "Source.md"
    Then I should receive 2 links
    And all links should be resolved

  Scenario: Get backlinks to document
    Given "Target.md" is linked from:
      | source          |
      | Doc A.md        |
      | Doc B.md        |
      | Doc C.md        |
    When I request backlinks for "Target.md"
    Then I should receive 3 backlinks

  Scenario: Sync links after document update
    Given "Source.md" links to "Target A"
    When I update "Source.md" to link to "Target B" instead
    Then "Source.md" should have 1 outgoing link to "Target B"
    And "Target A" should have 0 backlinks from "Source.md"
    And "Target B" should have 1 backlink from "Source.md"
```

### Feature: Semantic Search

```gherkin
Feature: Semantic Search
  As a user
  I want to search documents by meaning
  So that I can find relevant information

  Scenario: Search documents by semantic similarity
    Given documents exist:
      | title                    | content                                 |
      | Machine Learning Basics  | Introduction to ML algorithms           |
      | Cooking Recipes          | How to make pasta                       |
      | Deep Learning            | Neural networks and deep learning       |
    When I search for "artificial intelligence"
    Then "Machine Learning Basics" should be in the results
    And "Deep Learning" should be in the results
    And "Cooking Recipes" should not be in the results

  Scenario: Filter search by folder
    Given documents exist:
      | path                     | content                  |
      | AI/ML Basics.md          | Machine learning intro   |
      | Cooking/Pasta.md         | How to cook pasta        |
    When I search for "basics" filtered to folder "AI"
    Then only documents in "AI" folder should be returned
```

## 10.2 Unit Tests

### Domain Layer
- `test_wiki_link_parsing.py`: Parse all wiki-link variations
- `test_frontmatter_parsing.py`: Parse valid/invalid YAML
- `test_link_resolver.py`: Link resolution logic
- `test_tag_parser.py`: Tag extraction and hierarchy
- `test_document_path.py`: Path value object

### Application Layer
- `test_ingest_vault_use_case.py`: Vault ingestion flow
- `test_semantic_search_use_case.py`: Search orchestration
- `test_get_backlinks_use_case.py`: Backlink retrieval

## 10.3 Integration Tests

- `test_postgres_repositories.py`: Repository CRUD operations
- `test_pgvector_search.py`: Vector similarity search
- `test_age_graph_queries.py`: Cypher query execution
- `test_openai_embeddings.py`: Embedding generation (mocked)

## 10.4 Coverage Target

- Overall: ≥70%
- Domain Layer: ≥90%
- Application Layer: ≥80%
- Infrastructure Layer: ≥60%
- API Layer: ≥70%

## 10.5 Current Test Metrics (as of 2026-02-27)

| Category | Tests | Coverage |
|----------|-------|----------|
| Unit (Domain) | 77 | ~95% |
| Unit (Application) | 21 | ~85% |
| BDD Scenarios | 27 | N/A |
| API Tests | 32 | ~75% |
| Integration Tests | 27 | ~70% |
| **Total** | **205** | **~78%** |

---

# 11. Deployment Architecture

## 11.1 Docker Compose

```yaml
services:
  # Application server (use with: docker-compose --profile app up)
  app:
    profiles: ["app", "full"]
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://obsidian:obsidian@db:5432/obsidian
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - LOG_LEVEL=INFO
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./storage:/app/storage
    restart: unless-stopped

  # PostgreSQL 16 with pgvector + Apache AGE
  db:
    build:
      context: .
      dockerfile: Dockerfile.postgres  # Custom image with AGE
    environment:
      - POSTGRES_USER=obsidian
      - POSTGRES_PASSWORD=obsidian
      - POSTGRES_DB=obsidian
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"  # Port 5433 to avoid conflicts
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U obsidian -d obsidian"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
```

**Note:** The database uses a custom Dockerfile (`Dockerfile.postgres`) that builds PostgreSQL 16 with both pgvector and Apache AGE extensions compiled from source.

## 11.2 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| DATABASE_URL | PostgreSQL connection string | Yes |
| OPENAI_API_KEY | OpenAI API key for embeddings | Yes |
| JWT_SECRET | Secret for JWT signing | Yes |
| JWT_ALGORITHM | JWT algorithm (default: HS256) | No |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token expiry (default: 60) | No |
| LOG_LEVEL | Logging level (default: INFO) | No |

## 11.3 Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./

# Run migrations and start server
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

---

# 12. CI/CD Pipeline

## 12.1 GitHub Actions

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_obsidian
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Install dependencies
        run: uv sync

      - name: Run linting
        run: uv run ruff check .

      - name: Run type checking
        run: uv run mypy app

      - name: Run tests with coverage
        run: uv run pytest --cov=app --cov-report=xml --cov-fail-under=70
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_obsidian

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
```

---

# 13. Bridge System Integration

## 13.1 Alignment Points

The following design decisions enable future Bridge integration:

| Component | Alignment |
|-----------|-----------|
| `document_links` table | Matches Bridge document link schema |
| `embedding_chunks` table | Follows Bridge embedding pattern |
| Hexagonal architecture | Consistent with Bridge backend |
| JWT authentication | Compatible with Amini0 auth |
| MCP tools | Can be registered in Bridge tool catalog |

## 13.2 Future Integration Tasks

1. **Authentication Migration**: Replace local JWT with Amini0 tokens
2. **User ID Propagation**: Use Amini0 user IDs instead of local users
3. **Tool Registration**: Register MCP tools in Bridge catalog
4. **Cross-System Linking**: Enable `[[bridge:document-id]]` syntax
5. **Federated Search**: Unified search across Bridge and vaults

## 13.3 MCP Tool Registration

```python
# Future Bridge registration
bridge_tool_config = {
    "name": "obsidian-vault",
    "transport": "http",
    "endpoint_url": "https://vault.example.com/mcp",
    "tools": [
        "list_vaults",
        "get_document",
        "search_documents",
        "get_backlinks",
        "get_connections",
        "create_document",
        "update_document",
    ]
}
```

---

# 14. Glossary

| Term | Definition |
|------|------------|
| Vault | A collection of documents, folders, and metadata (an Obsidian vault) |
| Wiki-link | A link using `[[Target]]` syntax |
| Backlink | An incoming link from another document |
| Frontmatter | YAML metadata at the top of a Markdown file |
| Embed | A transclusion using `![[Target]]` syntax |
| Chunk | A portion of document content for embedding |
| AGE | Apache AGE, a PostgreSQL extension for graph queries |
| pgvector | PostgreSQL extension for vector similarity search |

---

# Appendix A: Example Frontmatter

```yaml
---
title: Machine Learning Basics
aliases:
  - ML Basics
  - Intro to ML
tags:
  - ai
  - machine-learning
  - tutorial
created: 2025-01-01
status: published
---
```

---

# Appendix B: Wiki-Link Regex Patterns

```python
# Standard wiki-link: [[Target]] or [[Target|Display]]
WIKI_LINK_PATTERN = r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'

# Embed: ![[Target]]
EMBED_PATTERN = r'!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'

# Heading link: [[Target#Heading]]
HEADING_LINK_PATTERN = r'\[\[([^#\]|]+)#([^\]|]+)(?:\|([^\]]+))?\]\]'

# Block link: [[Target#^block-id]]
BLOCK_LINK_PATTERN = r'\[\[([^#\]|]+)#\^([^\]|]+)(?:\|([^\]]+))?\]\]'

# Inline tag: #tag or #tag/subtag
TAG_PATTERN = r'(?<!\S)#([a-zA-Z][a-zA-Z0-9_/]*)'
```

---

---

# 15. Implementation Status

## 15.1 Current Test Coverage

| Test Suite | Count | Status |
|------------|-------|--------|
| Unit Tests (Domain) | 77 | ✓ Passing |
| Unit Tests (Application) | 21 | ✓ Passing |
| BDD Scenarios | 27 | ✓ Passing |
| API Tests | 32 | ✓ Passing |
| Integration Tests | 27 | ✓ Passing |
| **Total** | **205** | **✓ All Passing** |

## 15.2 Feature Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| User Registration/Login | ✓ Complete | JWT auth with refresh tokens |
| Vault CRUD | ✓ Complete | Create, read, delete vaults |
| Vault Ingestion (ZIP) | ✓ Complete | Full Obsidian vault parsing |
| Vault Export (ZIP) | ✓ Complete | Preserves folder structure |
| Document CRUD | ✓ Complete | With frontmatter support |
| Wiki-link Parsing | ✓ Complete | All syntax variants |
| Link Resolution | ✓ Complete | By title, alias, path |
| Backlinks | ✓ Complete | Automatic tracking |
| Tag Extraction | ✓ Complete | Frontmatter + inline |
| Hierarchical Tags | ✓ Complete | Tag tree with parent references |
| Semantic Search | ✓ Complete | OpenAI embeddings + pgvector |
| Full-text Search | ✓ Complete | PostgreSQL tsvector |
| Folder Filtering | ✓ Complete | In search and listings |
| Tag Filtering | ✓ Complete | In search |
| Apache AGE Graph | ✓ Complete | Nodes, edges, connections, hubs, orphans |
| MCP Server | ○ Pending | FastMCP integration planned |
| Attachments | ○ Pending | Image/PDF storage |

## 15.3 Verified E2E Test Results

Semantic search tested with real OpenAI API (2026-02-27):

```
Query: "neural networks and deep learning"
Results:
  1. Machine Learning Basics (score: 0.862) ✓ Best match
  2. Python Programming Guide (score: 0.735)
  3. Project Management (score: 0.719)
  4. Essential Cooking Tips (score: 0.691)

Query: "kitchen tools and recipes"
Results:
  1. Essential Cooking Tips (score: 0.855) ✓ Best match
  2. Project Management (score: 0.736)
  3. Machine Learning Basics (score: 0.712)
  4. Python Programming Guide (score: 0.701)
```

Semantic search correctly ranks documents by meaning, not just keywords.

## 15.4 Real Vault Test Results

Tested with "Leo Knowledge" vault (1018 documents, ~52MB):

**Import Performance:**
- Documents imported: 1018
- Links created: 8,773 (6,874 resolved)
- Graph nodes created: 1018
- Graph edges created: 391

**Semantic Search Results:**
```
Query: "machine learning and neural networks"
  1. Machine Learning (score: 0.851)
  2. Introduction to AI (score: 0.832)

Query: "blockchain cryptocurrency"
  1. Blockchain (score: 0.839)
  2. Bitcoin (score: 0.836)

Query: "Python programming"
  1. Python (score: 0.854)

Query: "physics mechanics"
  1. Physics (score: 0.844)
  2. Newton's Laws of Motion (score: 0.827)
```

**Graph Query Results:**
- Top connected documents: Mathematics (81), Machine Learning (57), Quadcopters (21)
- Orphan documents (no connections): 971

## 15.5 Directory Structure (Actual)

```
obsidian_vault_server/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry
│   ├── config.py                    # Pydantic settings
│   │
│   ├── domain/                      # Domain Layer
│   │   ├── entities/
│   │   │   ├── user.py
│   │   │   ├── vault.py
│   │   │   ├── document.py
│   │   │   ├── folder.py
│   │   │   ├── tag.py
│   │   │   ├── document_link.py
│   │   │   └── embedding_chunk.py
│   │   ├── value_objects/
│   │   │   ├── wiki_link.py
│   │   │   ├── frontmatter.py
│   │   │   └── document_path.py
│   │   ├── services/
│   │   │   ├── link_resolver.py
│   │   │   ├── tag_parser.py
│   │   │   └── markdown_processor.py
│   │   └── exceptions.py
│   │
│   ├── application/                 # Application Layer
│   │   ├── interfaces/
│   │   │   ├── repositories.py      # All repository ports
│   │   │   ├── embedding_provider.py
│   │   │   ├── graph_provider.py
│   │   │   └── storage.py
│   │   ├── use_cases/
│   │   │   ├── vault/
│   │   │   │   ├── create_vault.py
│   │   │   │   ├── delete_vault.py
│   │   │   │   ├── export_vault.py
│   │   │   │   ├── get_vault.py
│   │   │   │   ├── ingest_vault.py
│   │   │   │   └── list_vaults.py
│   │   │   ├── document/
│   │   │   │   ├── create_document.py
│   │   │   │   ├── delete_document.py
│   │   │   │   ├── get_document.py
│   │   │   │   ├── list_documents.py
│   │   │   │   └── update_document.py
│   │   │   ├── link/
│   │   │   │   ├── get_backlinks.py
│   │   │   │   ├── get_outgoing_links.py
│   │   │   │   └── sync_links.py
│   │   │   ├── search/
│   │   │   │   ├── semantic_search.py
│   │   │   │   └── fulltext_search.py
│   │   │   └── graph/
│   │   │       └── get_connections.py
│   │   └── dto/
│   │       ├── vault_dto.py
│   │       ├── document_dto.py
│   │       ├── link_dto.py
│   │       ├── search_dto.py
│   │       └── auth_dto.py
│   │
│   ├── infrastructure/              # Infrastructure Layer
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   ├── models/
│   │   │   │   ├── user.py
│   │   │   │   ├── vault.py
│   │   │   │   ├── document.py
│   │   │   │   ├── folder.py
│   │   │   │   ├── tag.py
│   │   │   │   ├── document_link.py
│   │   │   │   └── embedding_chunk.py
│   │   │   └── repositories/
│   │   │       ├── user_repository.py
│   │   │       ├── vault_repository.py
│   │   │       ├── document_repository.py
│   │   │       ├── folder_repository.py
│   │   │       ├── tag_repository.py
│   │   │       ├── link_repository.py
│   │   │       └── embedding_repository.py
│   │   ├── embedding/
│   │   │   └── openai_adapter.py
│   │   ├── storage/
│   │   │   └── local_storage.py
│   │   └── auth/
│   │       └── jwt_service.py
│   │
│   └── api/                         # API Layer
│       ├── dependencies.py
│       ├── routes/
│       │   ├── auth.py
│       │   ├── vaults.py
│       │   ├── documents.py
│       │   ├── search.py
│       │   └── graph.py
│       └── schemas/
│           ├── auth.py
│           ├── vault.py
│           ├── document.py
│           ├── link.py
│           ├── search.py
│           └── graph.py
│
├── migrations/
│   └── versions/
│       └── 001_initial_schema.py    # Complete schema
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   │   ├── test_entities.py
│   │   │   ├── test_value_objects.py
│   │   │   └── test_services.py
│   │   └── application/
│   │       └── test_use_cases.py
│   ├── bdd/
│   │   ├── features/
│   │   │   ├── vault_ingestion.feature
│   │   │   ├── document_linking.feature
│   │   │   ├── semantic_search.feature
│   │   │   └── vault_export.feature
│   │   └── step_defs/
│   │       ├── test_vault_ingestion.py
│   │       ├── test_document_linking.py
│   │       ├── test_semantic_search.py
│   │       └── test_vault_export.py
│   ├── api/
│   │   ├── test_auth_routes.py
│   │   ├── test_vault_routes.py
│   │   ├── test_document_routes.py
│   │   └── test_search_routes.py
│   └── integration/
│       ├── test_repositories.py
│       └── test_semantic_search_e2e.py
│
├── scripts/
│   ├── init-db.sql
│   └── test_semantic_search_e2e.py
│
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.postgres              # Custom PostgreSQL with pgvector + AGE
├── pyproject.toml
├── justfile
├── alembic.ini
└── .env
```

---

# 16. Quick Start Guide

## 16.1 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- OpenAI API key (for semantic search)

## 16.2 Setup

```bash
# Clone and enter directory
cd obsidian_vault_server

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start database
just db-up

# Run migrations
just migrate

# Start server
just dev
```

## 16.3 Test the API

```bash
# Register a user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123", "display_name": "Test"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
# Save the access_token from response

# Create/Ingest a vault
curl -X POST http://localhost:8000/vaults/my-vault/ingest \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@my-obsidian-vault.zip"

# Semantic search
curl -X POST http://localhost:8000/vaults/my-vault/search/semantic \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning concepts", "limit": 10}'
```

## 16.4 Run Tests

```bash
# All tests (may have event loop conflicts)
just test-all

# Recommended: Run test groups separately
just test-unit      # Unit tests only
just test-bdd       # BDD scenarios only
just test-api       # API tests (requires database)
just test-full      # Full cycle: start db, migrate, test, stop db
```

---

# Appendix C: Configuration Reference

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://obsidian:obsidian@localhost:5433/obsidian` | PostgreSQL connection |
| `OPENAI_API_KEY` | (required) | OpenAI API key for embeddings |
| `EMBEDDING_MODEL` | `text-embedding-ada-002` | OpenAI embedding model |
| `EMBEDDING_DIMENSIONS` | `1536` | Vector dimensions |
| `JWT_SECRET` | `change-me-in-production` | JWT signing secret |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token expiry |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token expiry |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEBUG` | `false` | Debug mode |
| `STORAGE_PATH` | `./storage` | File storage path |
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `CHUNK_SIZE` | `500` | Tokens per embedding chunk |
| `CHUNK_OVERLAP` | `50` | Token overlap between chunks |

---

# Appendix D: Docker Compose Configuration

```yaml
services:
  # Application server (use with: docker-compose --profile app up)
  app:
    profiles: ["app", "full"]
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://obsidian:obsidian@db:5432/obsidian
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - LOG_LEVEL=INFO
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./storage:/app/storage
    restart: unless-stopped

  # PostgreSQL with pgvector + Apache AGE (always starts with default profile)
  db:
    build:
      context: .
      dockerfile: Dockerfile.postgres
    environment:
      - POSTGRES_USER=obsidian
      - POSTGRES_PASSWORD=obsidian
      - POSTGRES_DB=obsidian
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U obsidian -d obsidian"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
```

**Usage:**

```bash
# Start database only (default)
docker-compose up -d

# Start full stack (database + app)
docker-compose --profile full up -d

# Using justfile commands
just db-up        # Start database
just db-down      # Stop database
just stack-up     # Start full stack
just stack-down   # Stop full stack
```

---

*Document Version: 1.2*
*Last Updated: 2026-02-27*
*Implementation Status: Core features + Apache AGE graph complete, MCP integration pending*
