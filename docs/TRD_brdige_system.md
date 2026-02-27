# Technical Requirements Document (TRD)

Project: AI Bridge Platform Architecture: FastAPI (Hexagonal),
PostgreSQL, Svelte 5 (MVVM) Deployment: Docker Compose (Coolify) Quality
Standard: BDD + TDD with ≥70% Test Coverage Target MVP Delivery: End of
March

------------------------------------------------------------------------

# 1. Introduction

This document defines the complete technical requirements for the AI
Bridge Platform.

The platform combines:

-   LLM-powered conversational AI (AminiLLM in production, ChatGPT in development)
-   Attachable MCP tools per chat
-   Markdown document authoring with inline comments
-   Obsidian-style folder organization
-   RAG (Retrieval-Augmented Generation)
-   Admin tool & permission control
-   Centralized authentication via Amini0 Auth Service
-   AWS IAM-style permissions via NFT IAM smart contracts on Aminichain
-   Containerized deployment
-   Mandatory BDD + TDD quality enforcement

The system is designed for scalability, maintainability, and clean
separation of concerns using Hexagonal Architecture. The frontend follows
a thin-client model where new functionality is delivered through MCP tools,
minimizing frontend changes and enabling rapid feature iteration.

------------------------------------------------------------------------

# 2. High-Level Architecture

## Core Stack

-   Backend: FastAPI (Hexagonal Architecture)
-   Database: PostgreSQL (optional pgvector extension)
-   Frontend: Svelte 5 (SPA using MVVM architecture) + Tailwind CSS
-   Background Processing: Worker service (Redis-backed queue)
-   Storage: S3-compatible (MinIO or cloud S3)
-   File Ingestion: Amini MMDI (Multimodal Data Ingestion) Service
-   Authentication: Amini0 Auth Service (centralized identity microservice)
-   Blockchain: Aminichain (Ethereum-compatible) for NFT-based permissions
-   LLM: AminiLLM (production) / ChatGPT (development)
-   Deployment: Docker Compose on Coolify

## Development Tooling

-   Package Manager (Python): [uv](https://github.com/astral-sh/uv) - Fast Python package installer
-   Package Manager (Node): npm / pnpm
-   Task Runner: [just](https://github.com/casey/just) - Command runner for project tasks
-   Database Migrations: Alembic
-   Linting: Ruff (Python), ESLint (TypeScript)
-   Formatting: Ruff (Python), Prettier (TypeScript)
-   Testing: pytest (Python), Vitest (TypeScript), Playwright (E2E)

------------------------------------------------------------------------

# 3. System Capabilities

## 3.1 ChatGPT-Style Chat

Users can:

-   Create and manage chat threads
-   Organize chats into folders
-   Stream AI responses (SSE)
-   Attach files (PDF, CSV, Images)
-   Enable/disable MCP tools per chat
-   View tool-call audit logs

------------------------------------------------------------------------

## 3.2 MCP Tool Attachment

Users (based on policy) can:

-   View tool catalog
-   Attach tools to specific chat threads
-   Detach tools
-   See which tools are active
-   View tool execution history

Admin controls:

-   Enable/disable tools globally
-   Assign tool access via group policies

## 3.2.1 User-Owned MCP Tools

Each user can maintain their own personal set of MCP tools, separate from the global catalog.

Users can:

-   Register personal MCP server endpoints (URL + authentication)
-   Register local process-based MCP servers (stdio transport)
-   Configure tool-specific settings and parameters
-   Manage a personal tool library
-   Share tools with other users (optional, permission-based)
-   Import tools from the global catalog into personal library
-   Set default tools to auto-attach on new chats

Personal tool management:

-   Each user's MCP servers run independently
-   Tool credentials are stored securely per user
-   Users are responsible for their own MCP server availability
-   Personal tools are validated before first use

Restrictions (based on NFT permissions):

-   Maximum number of personal tools allowed
-   Allowed MCP server domains/endpoints
-   Allowed commands for process-based tools (whitelist enforced)
-   Tool execution rate limits
-   Resource consumption quotas

## 3.2.2 MCP Transport Types

MCP tools support two transport types for communication:

### HTTP Transport (Default)

Remote MCP servers accessed via HTTP/HTTPS endpoints.

| Configuration | Description |
|--------------|-------------|
| `endpoint_url` | Full URL to the MCP server |
| `auth_type` | Authentication method (none, api_key, oauth, custom) |
| `auth_config` | Authentication credentials (encrypted) |

### STDIO Transport (Local Processes)

Local MCP servers running as subprocesses with JSON-RPC over stdin/stdout.

| Configuration | Description |
|--------------|-------------|
| `command` | Executable command (must be whitelisted) |
| `args` | Command-line arguments |
| `env_vars` | Environment variables for the process |
| `working_dir` | Working directory for process execution |
| `startup_timeout_ms` | Maximum startup time (default: 30000ms) |

**Example STDIO Configuration:**
```json
{
  "name": "context7",
  "transport_type": "stdio",
  "command": "npx",
  "args": ["-y", "@upstash/context7-mcp@latest"],
  "env_vars": {
    "API_KEY": "your-api-key"
  },
  "startup_timeout_ms": 60000
}
```

**Whitelisted Commands:**
Only approved commands can be used for process-based MCP servers:
- `npx` - Node.js package runner
- `node` - Node.js runtime
- `python` / `python3` - Python interpreter
- `uvx` - Python uv package runner
- `deno` - Deno runtime

### MCP Protocol Flow (STDIO)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Bridge    │     │   MCP       │     │   MCP       │
│   Platform  │────▶│   Router    │────▶│   Process   │
│   (Chat)    │     │             │     │   Client    │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                          │                   │
                          │                   │
                          │                   ▼
                          │            ┌─────────────┐
                          │            │   Local     │
                          │            │   MCP       │
                          │            │   Process   │
                          │            │  (stdin/out)│
                          │            └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   HTTP MCP  │
                   │   Client    │
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Remote    │
                   │   MCP       │
                   │   Server    │
                   └─────────────┘
```

The MCP Router automatically routes tool execution based on transport type:
1. **HTTP tools**: Sends HTTP requests to the MCP server endpoint
2. **STDIO tools**: Starts local process and communicates via JSON-RPC

For STDIO transport, the MCP Process Client handles:
1. Process lifecycle management (start, monitor, cleanup)
2. MCP handshake (`initialize` → `notifications/initialized`)
3. Tool discovery via `tools/list`
4. Tool execution via `tools/call`
5. Session caching for performance

------------------------------------------------------------------------

## 3.3 Markdown Authoring

Users can:

-   Create Markdown documents
-   Organize documents in folders
-   Auto-save edits
-   Maintain version history
-   Attach files to documents
-   Add threaded comments anchored to text ranges
-   Resolve/reopen comment threads
-   Use AI Writing Assistant for text completion and editing
-   Save chat responses as new documents
-   Create wiki-style links between documents using `[[Document Name]]` syntax
-   View document connections in the Document Graph Panel

### 3.3.1 AI Writing Assistant

The document editor includes an integrated AI Writing Assistant panel that helps users with text completion and editing without leaving the authoring view.

**Features:**

| Feature | Description |
|---------|-------------|
| **Complete at cursor** | AI continues writing from the current cursor position |
| **Replace selection** | AI rewrites the selected text based on instruction |
| **Quick prompts** | One-click actions: Continue, Expand, Simplify, Fix Grammar |
| **Contextual awareness** | AI sees surrounding text and document title for context |
| **Streaming responses** | Real-time token streaming via SSE |
| **Apply to document** | Insert AI response directly into the document |

**Modes:**

| Mode | Description |
|------|-------------|
| `complete` | Insert generated text at cursor position |
| `replace` | Replace selected text with generated content |

**Writing Context:**
The assistant receives contextual information:
- Document title
- Text before cursor (up to 500 chars)
- Text after cursor (up to 500 chars)
- Selected text (for replace mode)

**UI Components:**
- Collapsible right panel in document editor
- Mode toggle (Complete/Replace)
- Quick prompt buttons
- Message history with apply buttons
- Streaming content preview

### 3.3.2 Save Chat Response as Document

Users can save AI responses from chat conversations directly as new Authoring documents.

**Features:**

-   Save any assistant message from chat as a new document
-   Automatic title extraction from content
-   Optional folder selection for organization
-   Preserved markdown formatting from chat response
-   Direct navigation to newly created document

**Flow:**
1. User receives an AI response in chat
2. User clicks "Save as Document" on the message
3. Modal appears with title and folder selection
4. Document is created and user can navigate to it

### 3.3.3 Wiki-Style Document Linking

Documents can link to each other using wiki-style link syntax, enabling a connected knowledge base similar to Obsidian or Roam.

**Syntax:**
```markdown
Link to another document: [[Document Title]]
```

**Features:**

| Feature | Description |
|---------|-------------|
| **Auto-detection** | Links are parsed from `[[...]]` patterns in document content |
| **Auto-sync** | Links are automatically extracted and stored when documents are saved |
| **Manual sync** | Refresh links via the "Sync Links" button in the graph panel |
| **Bidirectional navigation** | View both outgoing links and backlinks (incoming links) |
| **Click to navigate** | Clicking a wiki-link navigates to the target document |
| **Create on navigate** | If the linked document doesn't exist, prompt to create it |

**Link Resolution:**
- Links are matched by exact document title (case-insensitive)
- Only documents owned by the same user are resolved
- Self-links (linking to the same document) are ignored
- Multiple links to the same document are deduplicated

**API Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/{id}/links/outgoing` | Get all outgoing links from a document |
| GET | `/documents/{id}/links/incoming` | Get all backlinks to a document |
| POST | `/documents/{id}/links/sync` | Manually trigger link extraction and sync |

### 3.3.4 Document Sharing and Review

Document authors can share documents with other users for collaborative review. Reviewers can view documents and add inline comments based on their permission level.

**Sharing Features:**

| Feature | Description |
|---------|-------------|
| **Email-based sharing** | Share documents by entering reviewer's email address |
| **Permission levels** | Three levels: read, comment, edit |
| **Expiration dates** | Optional expiration for time-limited access |
| **Share messages** | Optional message to include with the share invitation |
| **Revoke access** | Document owner can revoke access at any time |

**Permission Levels:**

| Level | Can View | Can Comment | Can Edit |
|-------|----------|-------------|----------|
| `read` | Yes | No | No |
| `comment` | Yes | Yes | No |
| `edit` | Yes | Yes | Yes |

**Reviewer Experience:**

- Dedicated "Shared with Me" section in navigation
- Read-only document view (or edit if permitted)
- Inline commenting on document text ranges
- Comment threads with replies
- View document owner information

**Author Experience:**

- Share button in document context menu
- Share modal with email input and permission selection
- View list of current shares for each document
- See reviewer comments on owned documents
- Resolve/reopen comment threads

**Access Control:**

- Share-based authorization integrated with comment system
- Expired shares automatically deny access
- Cannot share document with yourself
- Cannot create duplicate shares for same user
- Document owner retains full control

------------------------------------------------------------------------

## 3.4 Folder Organization (Obsidian-style)

Users can:

-   Create nested folders
-   Move chats and documents between folders
-   Browse folder tree
-   Filter content by folder
-   View wiki-link graph visualization (see 3.4.1)

Single folder model is shared across chats and documents.

### 3.4.1 Document Graph Visualization

The platform provides interactive graph visualizations for exploring document relationships and connections.

**Document Graph Panel (Author View):**

The Author view includes a Document Graph Panel that visualizes wiki-style links between documents.

| Feature | Description |
|---------|-------------|
| **Wiki-link connections** | Shows edges between documents linked via `[[Document Name]]` syntax |
| **Folder-based coloring** | Nodes are colored by their parent folder for visual organization |
| **Focused mode** | Centers on the current document and highlights immediate connections |
| **Global view** | Toggle to see all documents regardless of connections |
| **Interactive navigation** | Click nodes to navigate to documents |
| **Force-directed layout** | Automatic positioning with drag-and-drop support |
| **Zoom controls** | Zoom in/out and reset view |
| **Dynamic labels** | Labels adjust based on zoom level |

**Focused Mode:**

When viewing a document, the graph defaults to focused mode:
- Selected document is centered and highlighted
- Connected documents (via wiki links) are shown with a glow effect
- Unconnected documents are dimmed (20% opacity)
- Toggle button switches between focused and global views

**Accessing the Graph:**
- From sidebar: Click the Graph icon in the Files header
- From document editor: Click the Graph button in the toolbar
- Full-screen: Navigate to the dedicated `/graph` page

**Knowledge Graph Page:**

A dedicated `/graph` page provides a full-screen knowledge graph visualization:
- Depth controls (1-3 levels of connections)
- Shows documents, chats, and extracted concepts
- Interactive node exploration
- Navigation to source content

------------------------------------------------------------------------

## 3.5 NFT-Based Permissions (via Amini0 + NFT IAM Contracts)

User policies and permissions are derived from NFTs on the Aminichain blockchain (Ethereum-compatible),
using the NFT IAM smart contract system for AWS IAM-style fine-grained access control.

### 3.5.1 NFT IAM Smart Contracts

The permission system uses five smart contracts deployed on Aminichain:

| Contract | Purpose |
|----------|---------|
| **Identity** | ERC-721 NFT-based digital identity (one per user) |
| **Policy** | AWS IAM-style policy definition and evaluation engine |
| **Group** | Collection of identities with shared permissions |
| **Role** | Assumable roles with time-limited sessions |
| **PermissionBoundary** | Maximum permission limits per identity |

### 3.5.2 Three-Layer Permission Model

Permissions are evaluated through a three-layer model:

```
Layer 1: Identity Policies
    Direct policies attached to the user's NFT Identity
                    │
                    ▼
Layer 2: Group Policies
    Inherited policies from all groups the identity belongs to
                    │
                    ▼
Layer 3: Role Policies
    Policies from active role sessions (time-limited)
                    │
                    ▼
Permission Boundary (Intersection)
    Final = Effective Permissions ∩ Boundary Permissions
                    │
                    ▼
        Final Decision: ALLOW or DENY
```

### 3.5.3 Policy Evaluation Logic

Policies follow AWS IAM-style evaluation:

1. Collect all applicable policies (identity + groups + active roles)
2. For each policy, check statements against action/resource
3. If ANY statement explicitly denies → **DENY**
4. If ANY statement allows → **ALLOW**
5. Otherwise → **DENY** (default deny)
6. Intersect with Permission Boundary (if set)

### 3.5.4 ARN Format for Bridge Resources

Resources use Amazon Resource Name (ARN) format:

```
arn:amini:bridge:{region}:{account}:{resource-type}/{resource-id}
```

| Resource Type | ARN Pattern | Example |
|---------------|-------------|---------|
| Chat | `arn:amini:bridge:*:*:chat/*` | `arn:amini:bridge:us:123:chat/abc` |
| Document | `arn:amini:bridge:*:*:document/*` | `arn:amini:bridge:us:123:document/xyz` |
| Folder | `arn:amini:bridge:*:*:folder/*` | `arn:amini:bridge:us:123:folder/root` |
| MCP Tool | `arn:amini:bridge:*:*:tool/*` | `arn:amini:bridge:us:123:tool/global/*` |
| User Tool | `arn:amini:bridge:*:*:user-tool/*` | `arn:amini:bridge:us:123:user-tool/my-tool` |
| RAG Query | `arn:amini:bridge:*:*:rag/*` | `arn:amini:bridge:us:123:rag/search` |

### 3.5.5 Bridge Platform Actions

Actions that can be controlled via policies:

| Action | Description |
|--------|-------------|
| `bridge:CreateChat` | Create new chat thread |
| `bridge:DeleteChat` | Delete chat thread |
| `bridge:SendMessage` | Send message in chat |
| `bridge:CreateDocument` | Create new document |
| `bridge:EditDocument` | Edit document content |
| `bridge:DeleteDocument` | Delete document |
| `bridge:CreateFolder` | Create folder |
| `bridge:DeleteFolder` | Delete folder |
| `bridge:AttachTool` | Attach MCP tool to chat |
| `bridge:ExecuteTool` | Execute MCP tool |
| `bridge:RegisterTool` | Register personal MCP tool |
| `bridge:SearchRAG` | Perform RAG search query |
| `bridge:UploadFile` | Upload file attachment |
| `bridge:AdminAccess` | Access admin features |
| `bridge:*` | All actions (wildcard) |

### 3.5.6 Example Policy

```json
{
  "name": "BridgeStandardUser",
  "description": "Standard user access to Bridge Platform",
  "statements": [
    {
      "sid": "AllowChatOperations",
      "effect": "Allow",
      "actions": ["bridge:CreateChat", "bridge:SendMessage", "bridge:DeleteChat"],
      "resources": ["arn:amini:bridge:*:*:chat/*"],
      "conditions": []
    },
    {
      "sid": "AllowDocumentOperations",
      "effect": "Allow",
      "actions": ["bridge:CreateDocument", "bridge:EditDocument"],
      "resources": ["arn:amini:bridge:*:*:document/*"],
      "conditions": []
    },
    {
      "sid": "LimitToolUsage",
      "effect": "Allow",
      "actions": ["bridge:AttachTool", "bridge:ExecuteTool"],
      "resources": ["arn:amini:bridge:*:*:tool/global/*"],
      "conditions": [
        {"operator": "NumericLessThan", "key": "bridge:ToolExecutionsPerDay", "value": "100"}
      ]
    },
    {
      "sid": "DenyAdminAccess",
      "effect": "Deny",
      "actions": ["bridge:AdminAccess"],
      "resources": ["arn:amini:bridge:*:*:*"],
      "conditions": []
    }
  ]
}
```

### 3.5.7 Integration Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐
│   User      │    │   Amini0    │    │   Aminichain            │
│   Browser   │    │   Auth      │    │   (NFT IAM Contracts)   │
└──────┬──────┘    └──────┬──────┘    └───────────┬─────────────┘
       │                  │                       │
       │ 1. Authenticate  │                       │
       │─────────────────>│                       │
       │                  │                       │
       │                  │ 2. Check/Mint NFT    │
       │                  │ Identity              │
       │                  │──────────────────────>│
       │                  │                       │
       │ 3. JWT (with     │                       │
       │    identity_id)  │                       │
       │<─────────────────│                       │
       │                  │                       │
       │                                          │
       │ 4. API Request (JWT)                     │
       │─────────────────────────────────────────>│
       │           Bridge Platform                │
       │                  │                       │
       │                  │ 5. Evaluate           │
       │                  │ Permission            │
       │                  │ (on-chain call)       │
       │                  │──────────────────────>│
       │                  │                       │
       │                  │ 6. ALLOW/DENY         │
       │                  │<──────────────────────│
       │                  │                       │
       │ 7. Response      │                       │
       │<─────────────────│                       │
       │                  │                       │
```

### 3.5.8 NFT Identity Status

User access depends on NFT Identity status:

| Status | Value | Effect |
|--------|-------|--------|
| Active | 0 | Full access per policies |
| Suspended | 1 | No access (temporary) |
| Revoked | 2 | No access (permanent) |

### 3.5.9 Benefits

-   **AWS IAM-style control**: Familiar policy syntax with conditions
-   **On-chain auditability**: All permission changes recorded on blockchain
-   **Three-layer flexibility**: Direct, group, and role-based permissions
-   **Permission boundaries**: Prevent privilege escalation
-   **Transferable identities**: NFT-based identity can be transferred (if enabled)
-   **Decentralized storage**: Policies stored on Aminichain, not centralized DB
-   **Cross-service SSO**: Same identity across all Amini services

See [NFT IAM TRD](TRD_nft_iam.md) for detailed smart contract specifications.

------------------------------------------------------------------------

## 3.6 Multimodal Data Ingestion (MMDI) Integration

The Bridge Platform uses the Amini MMDI (Multimodal Data Ingestion) Service for all file uploads
and document processing. This external service converts various file formats into structured
markdown text suitable for LLM consumption and RAG indexing.

### 3.6.1 MMDI Service Overview

MMDI is a document processing microservice that provides:

-   **Multi-format Support:** PDF, DOCX, XLSX, CSV, images, and video
-   **Asynchronous Processing:** Background job queue for heavy processing
-   **LLM Enhancement:** Optional AI-powered image descriptions
-   **Multiple Storage Backends:** Local filesystem, IPFS, and Arweave
-   **Webhook Notifications:** Real-time completion callbacks
-   **Blockchain Integration:** Optional on-chain content registration

### 3.6.2 MMDI API Endpoints

Base URL: `https://mmdi-rest.bbd.prd.amini.ai/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/jobs/` | Submit document for processing |
| GET | `/jobs/{job_id}` | Get job status and details |
| GET | `/context/{job_id}` | Get extracted markdown content |
| GET | `/original/{job_id}` | Download original uploaded file |
| GET | `/system/status` | Health check |

### 3.6.3 Job Submission

**Request:**
```http
POST /api/v1/jobs/
Content-Type: multipart/form-data

uploaded_file: <file>
quality_level: 2 (1-4, optional)
webhook_url: https://bridge.amini.ai/webhooks/mmdi (optional)
```

**Response:**
```json
{
  "result": "success",
  "message": "Job queued successfully",
  "data": {
    "id": "01923e45-6789-7abc-def0-123456789abc",
    "status": "PENDING",
    "created_at": "2026-02-18T10:00:00Z",
    "quality_level": 2
  }
}
```

### 3.6.4 Job Status Values

| Status | Description |
|--------|-------------|
| PENDING | Job created, awaiting processing |
| STARTED | Job picked up by worker |
| COMPLETED | Processing finished successfully |
| FAILED | Processing encountered an error |

### 3.6.5 Content Retrieval

Once a job is COMPLETED, the extracted markdown is available:

**Request:**
```http
GET /api/v1/context/{job_id}
```

**Response:**
```json
{
  "context": "# Document Title\n\nExtracted content...\n\n---\n\n## Ingestion References\n- **Job ID:** 01923e45-6789...\n- **Wallet Address:** 0x1234..."
}
```

### 3.6.6 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Bridge Platform                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐│
│  │   Frontend   │────▶│   Backend    │────▶│   MMDI Adapter           ││
│  │   (Upload)   │     │   API        │     │   (Infrastructure)       ││
│  └──────────────┘     └──────────────┘     └───────────┬──────────────┘│
│                              │                         │                │
│                              │                         │                │
│                              ▼                         ▼                │
│                       ┌──────────────┐         ┌──────────────┐        │
│                       │  PostgreSQL  │         │    MMDI      │        │
│                       │ (attachment  │         │   Service    │        │
│                       │  records)    │         │  (External)  │        │
│                       └──────────────┘         └──────────────┘        │
│                              │                         │                │
│                              │   Webhook/Poll          │                │
│                              │◀────────────────────────┘                │
│                              │                                          │
│                              ▼                                          │
│                       ┌──────────────┐                                  │
│                       │  RAG Worker  │                                  │
│                       │ (Embeddings) │                                  │
│                       └──────────────┘                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.6.7 Webhook Integration

Bridge Platform registers a webhook URL when submitting jobs to MMDI.
When processing completes, MMDI sends a POST request to the webhook.

**Webhook Endpoint:**
```http
POST /webhooks/mmdi
Content-Type: application/json

{
  "job_id": "01923e45-6789-7abc-def0-123456789abc",
  "status": "COMPLETED",
  "output": {
    "md_text": "# Extracted Content...",
    "quality": "BALANCED"
  }
}
```

**Bridge Platform Response:**
1. Validates webhook authenticity
2. Updates attachment record status
3. Triggers RAG embedding generation
4. Notifies connected clients (SSE/WebSocket)

### 3.6.8 Supported File Types

| Category | Extensions | Notes |
|----------|------------|-------|
| Documents | PDF, DOCX | Full text and image extraction |
| Spreadsheets | XLSX, CSV | Table-to-markdown conversion |
| Images | PNG, JPG, GIF | OCR + optional AI description |
| Video | MP4, MOV | Placeholder for future support |

### 3.6.9 Error Handling

If MMDI processing fails:

1. Bridge receives FAILED status via webhook or polling
2. Attachment record updated with error message
3. User notified of failure
4. Retry available (max 3 attempts with different quality levels)

### 3.6.10 MCP Tool Access

MMDI also provides an MCP (Model Context Protocol) server for AI agent access:

-   **MCP Endpoint:** `https://mmdi-mcp.bbd.prd.amini.ai/mcp`
-   **Tool:** `get_context(job_id)` - Retrieve extracted markdown
-   **Resource:** `content://{job_id}` - MCP resource URI

This enables LLM agents attached to chats to directly access processed document content.

See [MMDI TRD](TRD_MMDI.md) for detailed service specifications.

------------------------------------------------------------------------

## 3.7 Amini RAG Integration (MCP Service)

The Bridge Platform can optionally integrate with the **Amini Ingestion KGraph** (Amini RAG) service
for advanced knowledge graph-based Retrieval-Augmented Generation queries. This is an external MCP
service that users can attach to their chats, separate from the platform's built-in document/chat search.

### 3.7.1 Important Distinction: Local Search vs Amini RAG

The Bridge Platform has **two independent search/retrieval systems**:

| Feature | Local Search | Amini RAG (MCP) |
|---------|--------------|-----------------|
| **Scope** | Bridge Platform content only | External knowledge graphs |
| **Data Source** | `documents`, `chat_messages`, `attachments` tables | Amini RAG projects (ingested documents) |
| **Technology** | pgvector embeddings on local content | LightRAG knowledge graph + pgvector |
| **Availability** | Always available | Optional MCP tool attachment |
| **Query Types** | Semantic search over user's documents/chats | Multi-mode RAG (local, global, hybrid, naive, mix) |
| **Knowledge Graph** | No | Yes (entities, relationships) |
| **Citations** | Document/message references | Confidence-scored citations with excerpts |

### 3.7.2 Amini RAG as MCP Service

Amini RAG is accessed via MCP (Model Context Protocol), allowing users to:

-   Attach the Amini RAG tool to specific chat threads
-   Query external knowledge graphs during conversations
-   Get confidence-scored answers with citations
-   Use different RAG modes (local, global, hybrid, naive, mix)

The service is **optional** - users who don't need external knowledge graph queries
can simply use the platform's built-in document/chat search.

### 3.7.3 Amini RAG MCP Endpoints

| Endpoint Type | URL | Description |
|---------------|-----|-------------|
| **REST API** | `https://amini-rag.bbd.prd.amini.ai:8000` | REST API for document management |
| **MCP Server** | `https://amini-rag.bbd.prd.amini.ai:8001` | MCP protocol endpoint |

### 3.7.4 Available MCP Tools

When the Amini RAG tool is attached to a chat, the LLM can use these tools:

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_projects` | List available RAG projects | `active_only`, `limit` |
| `list_datasources` | List files in a project | `project_slug` |
| `query_knowledge_graph` | Execute RAG query | `project_slug`, `query`, `mode` |

### 3.7.5 RAG Query Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **local** | Chunk-specific vector search | Find specific document passages |
| **global** | Knowledge graph traversal | Understand overall themes |
| **hybrid** | Combined local + global | Best overall results (recommended) |
| **naive** | Simple retrieval | Quick, basic queries |
| **mix** | Multiple strategies combined | Complex analytical queries |

### 3.7.6 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Bridge Platform                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐│
│  │   Chat UI    │────▶│   LLM with   │────▶│   MCP Tool Executor      ││
│  │  (User msg)  │     │   MCP Tools  │     │   (Amini RAG attached)   ││
│  └──────────────┘     └──────────────┘     └───────────┬──────────────┘│
│                                                        │                │
│         ┌──────────────────────────────────────────────┤                │
│         │                                              │                │
│         ▼                                              ▼                │
│  ┌──────────────┐                              ┌──────────────┐        │
│  │ Local Search │                              │  Amini RAG   │        │
│  │  (pgvector)  │                              │ MCP Server   │        │
│  │ documents,   │                              │  (External)  │        │
│  │ chats, etc.  │                              └──────────────┘        │
│  └──────────────┘                                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.7.7 Amini RAG Tool Registration

Amini RAG is registered as a **global MCP tool** by administrators:

```json
{
  "name": "amini_rag",
  "description": "Query Amini knowledge graphs for RAG-enhanced responses with citations",
  "endpoint_url": "https://amini-rag.bbd.prd.amini.ai:8001",
  "auth_type": "api_key",
  "input_schema": {
    "type": "object",
    "properties": {
      "project_slug": {"type": "string", "description": "Target knowledge graph project"},
      "query": {"type": "string", "description": "The question to answer"},
      "mode": {"type": "string", "enum": ["local", "global", "hybrid", "naive", "mix"], "default": "hybrid"}
    },
    "required": ["project_slug", "query"]
  },
  "requires_permission": "bridge:SearchRAG"
}
```

### 3.7.8 Response Format

Amini RAG returns structured responses with confidence scoring:

```json
{
  "result": "The answer to the query...",
  "query": "Original question",
  "mode": "hybrid",
  "processing_time_seconds": 2.5,
  "confidence": 0.85,
  "citations": [
    {
      "document_id": "doc_123",
      "filename": "report.pdf",
      "excerpt": "First 300 characters of relevant passage...",
      "similarity_score": 0.92
    }
  ],
  "sources": ["report.pdf", "analysis.docx"]
}
```

### 3.7.9 Permission Control

Access to Amini RAG is controlled via NFT IAM policies:

| Action | Description |
|--------|-------------|
| `bridge:AttachTool` | Permission to attach the Amini RAG tool |
| `bridge:ExecuteTool` | Permission to execute tool queries |
| `bridge:SearchRAG` | Specific permission for RAG operations |

Example policy restricting RAG usage:

```json
{
  "sid": "AllowAminiRAG",
  "effect": "Allow",
  "actions": ["bridge:SearchRAG"],
  "resources": ["arn:amini:bridge:*:*:rag/*"],
  "conditions": [
    {"operator": "NumericLessThan", "key": "bridge:RAGQueriesPerDay", "value": "100"}
  ]
}
```

### 3.7.10 When to Use Which

| Scenario | Recommended |
|----------|-------------|
| Search user's own documents/chats | Local Search |
| Query external knowledge bases | Amini RAG |
| Find specific text in authored content | Local Search |
| Cross-reference multiple document sources | Amini RAG |
| Simple keyword-based lookup | Local Search |
| Complex analytical questions | Amini RAG (mix mode) |
| Get citations with confidence scores | Amini RAG |

See [Amini RAG TRD](TRD_AMINI_RAG.md) for detailed service specifications.

------------------------------------------------------------------------

## 3.8 Large Language Model Integration

The platform uses LLMs with MCP tool-calling capabilities to power the chat
interface and document authoring features.

LLM Requirements:

-   Must support MCP (Model Context Protocol) tool usage
-   Must support streaming responses (SSE)
-   Must handle multi-turn conversations with context
-   Must support function/tool calling for MCP integration

Environment-Specific LLMs:

Development:
-   Provider: OpenAI
-   Model: ChatGPT (GPT-4 or latest available)
-   Purpose: Development, testing, and prototyping
-   Rationale: Well-documented API, reliable, easy to integrate

Production:
-   Provider: Amini
-   Model: AminiLLM (Amini proprietary LLM)
-   Purpose: Production workloads
-   Rationale: Proprietary model optimized for the platform, cost control,
    data sovereignty

LLM Usage Areas:

-   Chat conversations with tool invocation
-   Document authoring assistance (suggestions, completion, editing)
-   AI Writing Assistant (stateless text completion and replacement)
-   RAG-enhanced responses using embedded documents
-   Tool orchestration and multi-step reasoning

Architecture Considerations:

-   LLM adapter layer abstracts provider differences
-   Easy switching between providers via configuration
-   Consistent MCP tool interface regardless of LLM backend
-   Response streaming handled uniformly across providers
-   Token usage tracking and rate limiting per user (NFT-based quotas)

------------------------------------------------------------------------

# 4. Backend Architecture (Hexagonal)

Architectural Principles:

-   Domain layer is framework-independent
-   Use Cases orchestrate business logic
-   Adapters implement infrastructure details
-   FastAPI only exposes entrypoints

## 4.1 Backend Responsibilities

The backend is responsible for all data persistence, business logic, and
external service integrations. The frontend is a thin client that relies
entirely on the backend for state management and processing.

### 4.1.1 Authentication & Authorization (via Amini0)

Authentication is delegated to Amini0 Auth Service. Bridge Platform is a client of Amini0.

Amini0 handles:

-   User registration (email/password, OAuth, wallet SIWE)
-   JWT token generation (access + refresh tokens)
-   Session management and token refresh
-   NFT Identity minting on Aminichain
-   IAM policies and groups (on-chain)
-   Password reset and email verification

Bridge Platform handles:

-   JWT token validation (using Amini0's public key or shared secret)
-   User profile linking (Amini0 user_id → local user record)
-   NFT IAM permission evaluation (on-chain or cached)
-   Three-layer permission model enforcement (identity → group → role)
-   Permission boundary intersection for final access decision
-   Permission cache management (TTL-based, webhook invalidation)
-   First-login user provisioning (create local user on first valid token)

### 4.1.2 User Management

-   User registration and profile storage
-   Wallet address linking and management
-   User settings and preferences persistence
-   User quota tracking (based on NFT attributes)
-   Account deactivation and data export

User Settings include:

-   Default LLM preferences
-   UI preferences (theme, language)
-   Default MCP tools to auto-attach
-   Notification preferences
-   Privacy settings

### 4.1.3 Conversation Context Management

-   Chat thread creation and lifecycle management
-   Message persistence (user messages and LLM responses)
-   Conversation context storage for multi-turn interactions
-   Context window management (truncation, summarization)
-   Chat thread metadata (title, folder, timestamps)
-   Message streaming state management
-   Conversation export and import

Context Storage:

-   Full message history per chat thread
-   System prompts and instructions
-   Attached MCP tools state per conversation
-   File attachments linked to messages
-   Tool call history and results within conversation

### 4.1.4 Content Creation & Document Management

-   Document creation, update, and deletion
-   Auto-save with debouncing (periodic persistence)
-   Version history management (snapshots)
-   Document metadata (title, folder, tags, timestamps)
-   Document linking (wiki-style links between documents)
-   Content search and indexing
-   Document export (Markdown, PDF)

Version Control:

-   Automatic versioning on significant changes
-   Manual version creation (user-triggered snapshots)
-   Version comparison and rollback
-   Version retention policy enforcement

### 4.1.5 Folder Organization

-   Folder CRUD operations
-   Nested folder hierarchy management
-   Item (chat/document) movement between folders
-   Folder sharing and permissions (future)
-   Folder metadata and settings

### 4.1.6 Comment System

-   Comment thread creation anchored to text ranges
-   Comment CRUD operations
-   Thread resolution and reopening
-   Comment notifications
-   Comment history and audit trail
-   Share-based authorization for commenting

### 4.1.6.1 Document Sharing

-   Share documents with other users via email
-   Permission levels: read, comment, edit
-   Optional expiration dates for shares
-   Share revocation by document owner
-   List documents shared with current user
-   Access shared documents based on permission level
-   Integration with comment system for reviewer commenting

### 4.1.7 MCP Tool Management

-   Global tool catalog management (admin)
-   User personal tool registration and configuration
-   Tool attachment/detachment per chat
-   Tool credential storage (encrypted, per-user)
-   Tool execution orchestration
-   Tool call logging and audit trail
-   Tool sharing between users

Tool Execution:

-   Request validation against tool schema
-   Credential injection for tool calls
-   Timeout and error handling
-   Response parsing and formatting
-   Rate limiting per user (NFT-based)

### 4.1.8 LLM Integration

-   LLM provider abstraction (OpenAI, AminiLLM)
-   Request formatting per provider
-   Streaming response handling (SSE)
-   Token counting and usage tracking
-   Context window optimization
-   MCP tool call parsing and execution
-   Response caching (where applicable)

### 4.1.9 File Attachment Handling (via MMDI)

File uploads and document ingestion are delegated to the Amini MMDI (Multimodal Data Ingestion) Service.

MMDI handles:

-   File upload and validation
-   Multi-format document processing (PDF, DOCX, XLSX, CSV, images, video)
-   Markdown extraction with AI-powered image descriptions
-   Background job queue for heavy processing
-   Webhook notifications on completion
-   Content storage (local, IPFS, or Arweave)

Bridge Platform handles:

-   Proxying upload requests to MMDI
-   Tracking MMDI job IDs in local database
-   Polling/webhook integration for job status
-   Linking extracted content to messages/documents
-   Access control and permission validation
-   Triggering RAG embedding generation after MMDI completion

Integration Flow:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   Bridge    │────▶│    MMDI     │
│   Upload    │     │   Backend   │     │   Service   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           │ Store job_id      │ Process file
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  PostgreSQL │     │  Background │
                    │  (job ref)  │     │   Worker    │
                    └─────────────┘     └─────────────┘
                           │                   │
                           │                   │ Webhook/Poll
                           │◀──────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  RAG Index  │
                    │ (Embeddings)│
                    └─────────────┘
```

### 4.1.10 RAG & Search (Two Systems)

The Bridge Platform has **two independent search/retrieval systems**:

#### Local Search (Built-in)

For searching user-authored content within the Bridge Platform.

Document text extraction is delegated to MMDI. Bridge Platform handles embedding and retrieval.

MMDI provides:

-   Text extraction from all supported formats (PDF, DOCX, XLSX, CSV, images via OCR)
-   AI-powered image descriptions (when LLM enabled)
-   Structured markdown output with metadata

Bridge Platform handles:

-   Receiving extracted markdown from MMDI (via webhook or polling)
-   Chunking markdown content for embedding
-   Embedding generation (OpenAI/AminiLLM embeddings API)
-   Vector storage (pgvector)
-   Semantic search and retrieval over `documents`, `chat_messages`, `attachments`
-   Context augmentation for LLM queries
-   Embedding refresh when MMDI reprocesses documents

#### Amini RAG (Optional MCP Service)

For querying external knowledge graphs via MCP tool attachment.

When the Amini RAG tool is attached to a chat:

-   LLM can query external knowledge graph projects
-   Returns confidence-scored answers with citations
-   Supports multiple RAG modes (local, global, hybrid, naive, mix)
-   Uses LightRAG for knowledge graph traversal
-   Completely separate from local document/chat content

**Important**: Amini RAG queries external projects managed by the Amini RAG service,
NOT the user's documents/chats in the Bridge Platform. Users who want to search
their own authored content should use the Local Search feature.

See section 3.7 for Amini RAG integration details.

### 4.1.11 Background Processing

Document ingestion (PDF, DOCX, CSV, images, video) is handled by MMDI service.
Bridge Platform workers handle post-processing and platform-specific tasks.

Bridge Platform Workers:

-   Job queue management (Redis-backed)
-   Embedding generation workers (triggered after MMDI completion)
-   Document export workers
-   Scheduled tasks (NFT sync, MMDI job status polling, cleanup)
-   Job status tracking and retry logic
-   MMDI webhook handlers

MMDI Service Workers (external):

-   PDF/DOCX/XLSX/CSV processing
-   Image OCR and AI description
-   Video processing (future)
-   Blockchain content registration (optional)

### 4.1.12 Audit & Logging

-   Tool call audit trail
-   User action logging
-   Security event logging
-   API request/response logging
-   Error tracking and alerting
-   Usage metrics collection

### 4.1.13 API Layer

-   RESTful endpoints for CRUD operations
-   SSE endpoints for streaming responses
-   WebSocket support (future: real-time collaboration)
-   Request validation and sanitization
-   Rate limiting and throttling
-   CORS and security headers
-   API versioning

## 4.2 API Endpoints Specification

All endpoints are prefixed with `/api/v1`. Authentication required unless noted.

### 4.2.1 Authentication (Amini0 Integration)

Authentication is handled by Amini0 Auth Service. Bridge Platform validates Amini0-issued JWTs.

Direct Amini0 Endpoints (frontend calls Amini0 directly):

| Method | Amini0 Endpoint | Description |
|--------|-----------------|-------------|
| POST | `/api/v1/auth/register` | Register with email/password |
| POST | `/api/v1/auth/login` | Login with email/password |
| POST | `/api/v1/auth/wallet/challenge` | Get SIWE challenge for wallet auth |
| POST | `/api/v1/auth/wallet/verify` | Verify wallet signature, return JWT |
| GET | `/api/v1/auth/oauth/{provider}` | Initiate OAuth flow (google, microsoft) |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout current session |

Bridge Platform Endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/me` | Get current user profile and permissions (validates Amini0 JWT) |
| POST | `/auth/link` | Link Amini0 account to Bridge user on first login |

### 4.2.2 Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/me` | Get current user profile |
| PATCH | `/users/me` | Update current user profile |
| GET | `/users/me/settings` | Get user settings |
| PATCH | `/users/me/settings` | Update user settings |
| GET | `/users/me/quota` | Get usage quota and limits |
| POST | `/users/me/export` | Request data export |

### 4.2.3 Folders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/folders` | List all folders (tree structure) |
| POST | `/folders` | Create folder |
| GET | `/folders/{id}` | Get folder details |
| PATCH | `/folders/{id}` | Update folder |
| DELETE | `/folders/{id}` | Delete folder |
| POST | `/folders/{id}/move` | Move folder to new parent |

### 4.2.4 Chat Threads

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/chats` | List chat threads |
| POST | `/chats` | Create chat thread |
| GET | `/chats/{id}` | Get chat thread with messages |
| PATCH | `/chats/{id}` | Update chat metadata |
| DELETE | `/chats/{id}` | Delete chat thread |
| POST | `/chats/{id}/move` | Move chat to folder |
| GET | `/chats/{id}/export` | Export chat as JSON/Markdown |

### 4.2.5 Chat Messages & Streaming

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chats/{id}/messages` | Send message, get LLM response |
| GET | `/chats/{id}/messages` | List messages (paginated) |
| GET | `/chats/{id}/stream` | SSE endpoint for streaming responses |
| DELETE | `/chats/{id}/messages/{msg_id}` | Delete message |
| POST | `/chats/{id}/regenerate` | Regenerate last LLM response |

### 4.2.6 MCP Tools

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tools` | List available tools (global + user) |
| GET | `/tools/global` | List global tool catalog |
| GET | `/tools/me` | List user's personal tools |
| POST | `/tools/me` | Register personal MCP tool |
| GET | `/tools/me/{id}` | Get personal tool details |
| PATCH | `/tools/me/{id}` | Update personal tool config |
| DELETE | `/tools/me/{id}` | Remove personal tool |
| POST | `/tools/me/{id}/test` | Test tool connection |

**Register Tool Request (HTTP Transport):**
```json
{
  "name": "my-tool",
  "description": "Tool description",
  "transport_type": "http",
  "endpoint_url": "https://mcp-server.example.com",
  "auth_type": "api_key",
  "input_schema": { "type": "object", "properties": {} }
}
```

**Register Tool Request (STDIO Transport):**
```json
{
  "name": "context7",
  "description": "Context7 MCP Server",
  "transport_type": "stdio",
  "command": "npx",
  "args": ["-y", "@upstash/context7-mcp@latest"],
  "env_vars": { "API_KEY": "your-key" },
  "startup_timeout_ms": 60000,
  "input_schema": { "type": "object", "properties": {} }
}
```

**Notes:**
- `transport_type` defaults to "http" if not specified
- For "stdio" transport, `command` must be in the whitelist
- `endpoint_url` is required for "http", `command` is required for "stdio"

### 4.2.7 Chat Tool Attachments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/chats/{id}/tools` | List attached tools |
| POST | `/chats/{id}/tools` | Attach tool to chat |
| DELETE | `/chats/{id}/tools/{tool_id}` | Detach tool from chat |
| GET | `/chats/{id}/tools/calls` | List tool call history |

### 4.2.8 Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents` | List documents |
| POST | `/documents` | Create document |
| GET | `/documents/{id}` | Get document content |
| PATCH | `/documents/{id}` | Update document (auto-save) |
| DELETE | `/documents/{id}` | Delete document |
| POST | `/documents/{id}/move` | Move document to folder |
| GET | `/documents/{id}/versions` | List version history |
| GET | `/documents/{id}/versions/{v}` | Get specific version |
| POST | `/documents/{id}/versions` | Create manual snapshot |
| POST | `/documents/{id}/restore/{v}` | Restore to version |
| GET | `/documents/{id}/export` | Export as Markdown/PDF |

### 4.2.8.1 Writing Assistant

Stateless AI writing assistance for document authoring.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/assistant/stream` | Stream AI writing assistance response |

**Request Body:**
```json
{
  "content": "Instruction with context for the AI",
  "system_prompt": "Optional custom system prompt"
}
```

**SSE Events:**

| Event | Payload | Description |
|-------|---------|-------------|
| `content` | `{"content": "...", "finish_reason": null}` | Streamed content chunk |
| `error` | `{"error": "...", "type": "..."}` | Error occurred |
| `done` | `{"finish_reason": "stop"}` | Stream completed |

**Notes:**
- This is a stateless endpoint (no chat history stored)
- Designed for quick completions and text edits
- Uses SSE (Server-Sent Events) for streaming
- Default system prompt is optimized for writing assistance

### 4.2.9 Comments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/{id}/comments` | List comment threads |
| POST | `/documents/{id}/comments` | Create comment thread |
| GET | `/comments/{id}` | Get comment thread |
| POST | `/comments/{id}/replies` | Add reply to thread |
| PATCH | `/comments/{id}` | Update comment |
| DELETE | `/comments/{id}` | Delete comment |
| POST | `/comments/{id}/resolve` | Resolve thread |
| POST | `/comments/{id}/reopen` | Reopen thread |

### 4.2.9.1 Document Sharing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/documents/{id}/shares` | Create document share |
| GET | `/documents/{id}/shares` | List shares for document |
| PATCH | `/documents/{id}/shares/{shareId}` | Update share permission/expiration |
| DELETE | `/documents/{id}/shares/{shareId}` | Revoke share |
| GET | `/shared-documents` | List documents shared with current user |
| GET | `/shared-documents/{id}` | Get shared document content |

**Create Share Request:**
```json
{
  "shared_with_email": "reviewer@example.com",
  "permission_level": "comment",
  "expires_at": "2025-12-31T23:59:59Z",
  "message": "Please review this document"
}
```

**Share Response:**
```json
{
  "id": "share-uuid",
  "document_id": "doc-uuid",
  "document_title": "My Document",
  "owner_id": "owner-uuid",
  "owner_name": "John Doe",
  "shared_with_id": "reviewer-uuid",
  "shared_with_name": "Jane Smith",
  "shared_with_email": "reviewer@example.com",
  "permission_level": "comment",
  "expires_at": "2025-12-31T23:59:59Z",
  "is_active": true,
  "message": "Please review this document",
  "created_at": "2025-02-22T12:00:00Z"
}
```

**Shared Document Response:**
```json
{
  "id": "doc-uuid",
  "title": "My Document",
  "content": "Document markdown content...",
  "owner_id": "owner-uuid",
  "owner_name": "John Doe",
  "permission_level": "comment",
  "can_comment": true,
  "can_edit": false,
  "created_at": "2025-02-22T12:00:00Z",
  "updated_at": "2025-02-22T12:00:00Z"
}
```

### 4.2.10 Attachments (via MMDI)

File uploads are proxied to the MMDI service for processing.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/attachments` | Upload file (proxied to MMDI) |
| GET | `/attachments/{id}` | Get attachment metadata and MMDI job status |
| GET | `/attachments/{id}/download` | Download original file (via MMDI) |
| GET | `/attachments/{id}/content` | Get extracted markdown content (from MMDI) |
| DELETE | `/attachments/{id}` | Delete attachment reference |
| GET | `/attachments/{id}/status` | Get MMDI ingestion job status |

**Upload Flow:**

1. Client uploads file to Bridge Platform
2. Bridge validates permissions and file type
3. Bridge proxies file to MMDI `POST /api/v1/jobs/`
4. MMDI returns `job_id` and `PENDING` status
5. Bridge stores attachment record with MMDI `job_id`
6. Bridge configures webhook URL for completion notification
7. When MMDI completes, Bridge receives webhook and triggers RAG indexing

**MMDI Quality Levels:**

| Level | Mode | Use Case |
|-------|------|----------|
| 1 | FASTEST | Quick preview, low quality |
| 2 | BALANCED | Default, good quality/speed tradeoff |
| 3 | TABLE_OPTIMIZED | Documents with complex tables |
| 4 | HIGHEST_QUALITY | Maximum extraction quality |

### 4.2.11 Local Search (Built-in)

Search within user's own documents, chats, and attachments using text and semantic search.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/search` | Unified search across documents, chats, and attachments |
| POST | `/search/chat/{id}` | Search within chat message history |
| POST | `/search/attachments` | Semantic search within attachment content |
| GET | `/search/ingestion/status` | Get embedding ingestion queue status |

**Unified Search Request (`POST /search`):**
```json
{
  "query": "search text",
  "types": ["document", "chat", "attachment"],
  "folder_id": "optional-folder-uuid",
  "limit": 20,
  "similarity_threshold": 0.5,
  "include_content": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Search query text (1-1000 chars) |
| `types` | array | Filter by content types (optional, default: all) |
| `folder_id` | string | Filter documents by folder (optional) |
| `limit` | int | Max results (1-50, default: 20) |
| `similarity_threshold` | float | Min similarity for attachments (0-1, default: 0.5) |
| `include_content` | bool | Include content snippets (default: true) |

**Unified Search Response:**
```json
{
  "query": "search text",
  "results": [
    {
      "id": "uuid",
      "type": "document",
      "title": "Document Title",
      "content": "matching content snippet...",
      "excerpt": "...context around match...",
      "score": 0.85,
      "created_at": "2025-01-15T10:30:00Z",
      "metadata": {
        "folder_id": "folder-uuid"
      }
    }
  ],
  "total": 5,
  "processing_time_ms": 42
}
```

| Result Type | Search Method | Score Calculation |
|-------------|---------------|-------------------|
| `document` | Text match (ILIKE) on title/content | 0.9 title match, 0.7 content match |
| `chat` | Text match (ILIKE) on chat title | 0.85 title match |
| `attachment` | Semantic (pgvector cosine similarity) | Similarity score from embedding |

**Note**: Local Search queries the Bridge Platform's internal content (documents,
chats, attachments). For external knowledge graph queries, use the Amini RAG
MCP tool via the chat interface.

### 4.2.12 Amini RAG (via MCP)

Amini RAG is accessed through MCP tool execution, not direct API endpoints.
When attached to a chat, the LLM can invoke RAG queries.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tools/amini-rag/status` | Check Amini RAG service availability |
| GET | `/tools/amini-rag/projects` | List available RAG projects |

RAG queries are executed via `POST /chats/{id}/messages` when the Amini RAG
tool is attached and the LLM decides to use it.

### 4.2.13 Webhooks

Internal endpoints for external service callbacks.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks/mmdi` | MMDI job completion callback |

**MMDI Webhook Payload:**
```json
{
  "job_id": "01923e45-6789-7abc-def0-123456789abc",
  "status": "COMPLETED",
  "output": {
    "md_text": "# Extracted Content...",
    "quality": "BALANCED",
    "extractor_used": "PyDocExtractor"
  }
}
```

**Webhook Security:**
- Validates `X-MMDI-Signature` header using shared secret
- Rejects requests with invalid or missing signatures
- Rate-limited to prevent abuse

### 4.2.14 Admin (requires admin NFT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/tools` | List all global tools |
| POST | `/admin/tools` | Add global tool |
| PATCH | `/admin/tools/{id}` | Update global tool |
| DELETE | `/admin/tools/{id}` | Remove global tool |
| GET | `/admin/users` | List users |
| GET | `/admin/audit` | View audit logs |
| GET | `/admin/metrics` | View usage metrics |

## 4.3 Error Handling Strategy

### 4.3.1 Standard Error Response Format

All API errors return a consistent JSON structure:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested chat thread was not found",
    "details": {
      "resource_type": "chat_thread",
      "resource_id": "123"
    },
    "request_id": "req_abc123"
  }
}
```

### 4.3.2 Error Codes

Authentication Errors (401):
- `AUTH_TOKEN_EXPIRED` - Amini0 JWT token has expired
- `AUTH_TOKEN_INVALID` - Amini0 JWT token is malformed or invalid
- `AUTH_AMINI0_UNAVAILABLE` - Amini0 Auth Service is unreachable
- `AUTH_USER_SUSPENDED` - User's NFT Identity is suspended in Amini0
- `AUTH_USER_REVOKED` - User's NFT Identity is revoked in Amini0

Authorization Errors (403):
- `PERMISSION_DENIED` - User lacks required permission
- `NFT_PERMISSION_MISSING` - Required NFT not found in wallet
- `QUOTA_EXCEEDED` - User has exceeded usage quota
- `TOOL_ACCESS_DENIED` - User cannot access this tool

Resource Errors (404):
- `RESOURCE_NOT_FOUND` - Requested resource does not exist
- `FOLDER_NOT_FOUND` - Folder does not exist
- `CHAT_NOT_FOUND` - Chat thread does not exist
- `DOCUMENT_NOT_FOUND` - Document does not exist
- `TOOL_NOT_FOUND` - MCP tool does not exist

Validation Errors (400):
- `VALIDATION_ERROR` - Request body validation failed
- `INVALID_FILE_TYPE` - Uploaded file type not allowed
- `FILE_TOO_LARGE` - File exceeds size limit
- `INVALID_TOOL_CONFIG` - MCP tool configuration invalid

Conflict Errors (409):
- `RESOURCE_CONFLICT` - Resource state conflict
- `VERSION_CONFLICT` - Document version conflict
- `DUPLICATE_RESOURCE` - Resource already exists

Server Errors (500):
- `INTERNAL_ERROR` - Unexpected server error
- `LLM_PROVIDER_ERROR` - LLM service unavailable
- `TOOL_EXECUTION_ERROR` - MCP tool execution failed
- `STORAGE_ERROR` - S3 storage operation failed
- `AMINI0_ERROR` - Amini0 Auth Service error
- `BLOCKCHAIN_ERROR` - Aminichain query failed (via Amini0)
- `MMDI_ERROR` - MMDI service unavailable or error
- `MMDI_PROCESSING_FAILED` - MMDI document processing failed
- `MMDI_TIMEOUT` - MMDI request timed out
- `AMINI_RAG_ERROR` - Amini RAG service unavailable or error
- `AMINI_RAG_PROJECT_NOT_FOUND` - Requested RAG project does not exist
- `AMINI_RAG_QUERY_FAILED` - RAG query execution failed
- `AMINI_RAG_TIMEOUT` - RAG query timed out

### 4.3.3 Error Handling by Layer

Domain Layer:
- Raise domain-specific exceptions
- No HTTP concepts in domain errors

Use Case Layer:
- Catch domain exceptions
- Transform to application errors with context

API Layer (FastAPI):
- Global exception handlers
- Map application errors to HTTP responses
- Log errors with request context

Frontend:
- Display user-friendly error messages
- Retry transient errors automatically
- Redirect to login on auth errors

------------------------------------------------------------------------

# 5. Database Design (PostgreSQL)

## 5.1 Overview

The database uses PostgreSQL 16 with the pgvector extension for RAG embeddings.
All tables use UUIDs as primary keys for distributed compatibility.

Naming Conventions:
- Tables: snake_case, plural (e.g., `chat_threads`)
- Columns: snake_case (e.g., `created_at`)
- Foreign keys: `{referenced_table_singular}_id` (e.g., `user_id`)
- Indexes: `idx_{table}_{column(s)}` (e.g., `idx_chat_threads_user_id`)

## 5.2 Auth & Authorization Tables (Amini0 Integration)

Authentication is handled by Amini0. Bridge Platform stores minimal user data and links to Amini0 user IDs.

### users

Primary user account table (linked to Amini0).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Bridge Platform user ID |
| `amini0_user_id` | UUID | UNIQUE, NOT NULL | Amini0 external user ID |
| `display_name` | VARCHAR(100) | | User display name (synced from Amini0) |
| `email` | VARCHAR(255) | NULL | Email (synced from Amini0, denormalized) |
| `avatar_url` | VARCHAR(500) | NULL | Profile picture URL |
| `default_wallet_address` | VARCHAR(42) | NULL | Primary wallet (synced from Amini0) |
| `is_active` | BOOLEAN | DEFAULT true | Account active status |
| `is_admin` | BOOLEAN | DEFAULT false | Admin flag (derived from Amini0 IAM) |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | First login to Bridge Platform |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update time |
| `last_login_at` | TIMESTAMPTZ | NULL | Last login timestamp |
| `amini0_synced_at` | TIMESTAMPTZ | NULL | Last sync with Amini0 |

Indexes:
- `idx_users_amini0_user_id` ON (amini0_user_id) - Primary lookup
- `idx_users_email` ON (email) WHERE email IS NOT NULL
- `idx_users_default_wallet` ON (lower(default_wallet_address)) WHERE default_wallet_address IS NOT NULL

Note: User creation happens automatically on first valid Amini0 JWT validation.
Profile data is synced from Amini0 periodically or on user request.

### user_settings

User preferences and configuration (non-permission related).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | UUID | FK → users, UNIQUE | One settings per user |
| `theme` | VARCHAR(20) | DEFAULT 'system' | UI theme (light/dark/system) |
| `language` | VARCHAR(10) | DEFAULT 'en' | Preferred language |
| `default_llm_model` | VARCHAR(50) | NULL | Preferred LLM model |
| `default_tool_ids` | UUID[] | DEFAULT '{}' | Auto-attach tools |
| `notifications_enabled` | BOOLEAN | DEFAULT true | Enable notifications |
| `email_notifications` | BOOLEAN | DEFAULT false | Email notifications |
| `auto_save_interval_ms` | INTEGER | DEFAULT 2000 | Document auto-save interval |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update time |

### nft_iam_permission_cache

Cached permissions derived from NFT IAM smart contracts on Aminichain.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | UUID | FK → users, NOT NULL | User reference |
| `nft_identity_id` | INTEGER | NOT NULL | NFT Identity token ID (on-chain) |
| `identity_status` | SMALLINT | NOT NULL | 0=Active, 1=Suspended, 2=Revoked |
| `identity_policies` | BYTEA[] | DEFAULT '{}' | Direct policy IDs (bytes32[]) |
| `group_ids` | INTEGER[] | DEFAULT '{}' | Group memberships (on-chain IDs) |
| `group_policies` | BYTEA[] | DEFAULT '{}' | Inherited group policy IDs |
| `active_role_ids` | INTEGER[] | DEFAULT '{}' | Active role session IDs |
| `role_policies` | BYTEA[] | DEFAULT '{}' | Role session policy IDs |
| `boundary_policy_id` | BYTEA | NULL | Permission boundary policy ID |
| `cached_at` | TIMESTAMPTZ | NOT NULL | Cache timestamp |
| `expires_at` | TIMESTAMPTZ | NOT NULL | Cache expiration (default 5min) |
| `chain_block_number` | BIGINT | NULL | Block number at cache time |

Indexes:
- `idx_nft_iam_cache_user_id` ON (user_id)
- `idx_nft_iam_cache_identity_id` ON (nft_identity_id)
- `idx_nft_iam_cache_expires_at` ON (expires_at)

Note: This cache stores the three-layer permission structure from NFT IAM contracts.
Permission evaluation can happen either:
1. On-chain via contract calls (authoritative, slower)
2. Off-chain using cached policies (fast, requires cache refresh)

### permission_evaluation_cache

Caches individual permission evaluation results for performance.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | UUID | FK → users, NOT NULL | User reference |
| `nft_identity_id` | INTEGER | NOT NULL | NFT Identity token ID |
| `action` | VARCHAR(100) | NOT NULL | Action being evaluated |
| `resource_arn` | VARCHAR(500) | NOT NULL | Resource ARN being accessed |
| `result` | BOOLEAN | NOT NULL | true=ALLOW, false=DENY |
| `evaluated_at` | TIMESTAMPTZ | NOT NULL | Evaluation timestamp |
| `expires_at` | TIMESTAMPTZ | NOT NULL | Result expiration |
| `evaluation_source` | VARCHAR(20) | NOT NULL | 'on_chain' or 'cached' |

Indexes:
- `idx_perm_eval_cache_lookup` ON (user_id, action, resource_arn)
- `idx_perm_eval_cache_expires` ON (expires_at)
- UNIQUE (user_id, action, resource_arn)

Note: Stores recent permission evaluation results to avoid repeated on-chain
calls for the same action/resource combination. Cache TTL is short (60 seconds).

### nft_groups_cache (Local Cache)

Local cache of NFT IAM Group contract data. Groups are managed on-chain.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `chain_group_id` | INTEGER | UNIQUE, NOT NULL | On-chain group ID |
| `name` | VARCHAR(100) | NOT NULL | Group name (from contract) |
| `description` | TEXT | NULL | Group description |
| `creator_address` | VARCHAR(42) | NOT NULL | Group creator address |
| `policy_ids` | BYTEA[] | DEFAULT '{}' | Attached policy IDs (bytes32[]) |
| `member_count` | INTEGER | DEFAULT 0 | Cached member count |
| `cached_at` | TIMESTAMPTZ | DEFAULT now() | Cache timestamp |

Note: Groups are managed on-chain via NFT IAM Group contract. This is a local
cache for UI display. Authoritative data is always on Aminichain.

### nft_policies_cache (Local Cache)

Local cache of NFT IAM Policy contract data. Policies are managed on-chain.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `chain_policy_id` | BYTEA | UNIQUE, NOT NULL | On-chain policy ID (bytes32) |
| `name` | VARCHAR(100) | NOT NULL | Policy name (from contract) |
| `description` | TEXT | NULL | Policy description |
| `creator_address` | VARCHAR(42) | NOT NULL | Policy creator address |
| `version` | INTEGER | DEFAULT 1 | Policy version number |
| `statements` | JSONB | NOT NULL | Policy statements (cached) |
| `cached_at` | TIMESTAMPTZ | DEFAULT now() | Cache timestamp |

Policy Statement Structure (JSONB):
```json
{
  "statements": [
    {
      "sid": "bytes32_hex",
      "effect": "Allow|Deny",
      "actions": ["bridge:*", "bridge:CreateChat"],
      "resources": ["arn:amini:bridge:*:*:chat/*"],
      "conditions": [
        {"operator": "NumericLessThan", "key": "key", "value": "100"}
      ]
    }
  ]
}
```

Note: Policies are managed on-chain via NFT IAM Policy contract. Bridge Platform
caches policy statements locally for efficient off-chain permission evaluation.

### NFT IAM Integration Notes

**On-Chain Source of Truth**: All IAM data is stored on Aminichain:
-   **Identity Contract**: User NFT identities (ERC-721)
-   **Policy Contract**: AWS IAM-style policies with statements
-   **Group Contract**: Identity groups with shared policies
-   **Role Contract**: Assumable roles with time-limited sessions
-   **PermissionBoundary Contract**: Maximum permission limits

**Permission Evaluation Options**:
1. **On-chain (authoritative)**: Call Policy contract's `evaluatePolicy()` directly
2. **Off-chain (cached)**: Evaluate against cached policies for performance

**Cache Refresh Strategy**:
-   Permission cache: TTL 5 minutes (configurable via `NFT_IAM_CACHE_TTL_SECONDS`)
-   Policy/Group cache: TTL 1 hour or on-demand refresh
-   Immediate invalidation on known state changes (via Amini0 webhooks)

See [NFT IAM TRD](TRD_nft_iam.md) for detailed smart contract specifications.

## 5.3 Folder Structure Tables

### folders

Hierarchical folder structure for organizing chats and documents.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | UUID | FK → users, NOT NULL | Owner user |
| `parent_id` | UUID | FK → folders, NULL | Parent folder (NULL = root) |
| `name` | VARCHAR(255) | NOT NULL | Folder name |
| `color` | VARCHAR(7) | NULL | Hex color code (#RRGGBB) |
| `icon` | VARCHAR(50) | NULL | Icon identifier |
| `sort_order` | INTEGER | DEFAULT 0 | Sort position |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update time |

Indexes:
- `idx_folders_user_id` ON (user_id)
- `idx_folders_parent_id` ON (parent_id)
- UNIQUE (user_id, parent_id, name) - No duplicate names in same folder

Constraints:
- CHECK (id != parent_id) - Prevent self-reference

## 5.4 MCP Tools Tables

### mcp_tools_global

Global MCP tool catalog (admin-managed).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `name` | VARCHAR(100) | UNIQUE, NOT NULL | Tool name |
| `description` | TEXT | NOT NULL | Tool description |
| `transport_type` | VARCHAR(10) | NOT NULL, DEFAULT 'http' | http or stdio |
| `endpoint_url` | VARCHAR(500) | NULL | MCP server endpoint (HTTP) |
| `auth_type` | VARCHAR(20) | NOT NULL | none/api_key/oauth/custom |
| `auth_config` | JSONB | NULL | Auth configuration (encrypted) |
| `command` | VARCHAR(200) | NULL | Executable command (STDIO) |
| `args` | JSONB | NULL | Command arguments (STDIO) |
| `env_vars` | JSONB | NULL | Environment variables (STDIO) |
| `working_dir` | VARCHAR(500) | NULL | Process working directory (STDIO) |
| `startup_timeout_ms` | INTEGER | DEFAULT 30000 | Process startup timeout (STDIO) |
| `input_schema` | JSONB | NOT NULL | JSON Schema for input |
| `output_schema` | JSONB | NULL | JSON Schema for output |
| `is_enabled` | BOOLEAN | DEFAULT true | Globally enabled |
| `requires_permission` | VARCHAR(100) | NULL | Required NFT permission |
| `rate_limit_rpm` | INTEGER | DEFAULT 60 | Requests per minute limit |
| `timeout_ms` | INTEGER | DEFAULT 30000 | Execution timeout |
| `created_by` | UUID | FK → users | Admin who created |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update time |

### user_mcp_tools

User's personal MCP tools.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | UUID | FK → users, NOT NULL | Owner user |
| `name` | VARCHAR(100) | NOT NULL | Tool name |
| `description` | TEXT | NULL | Tool description |
| `transport_type` | VARCHAR(10) | NOT NULL, DEFAULT 'http' | http or stdio |
| `endpoint_url` | VARCHAR(500) | NULL | MCP server endpoint (HTTP) |
| `auth_type` | VARCHAR(20) | NOT NULL | none/api_key/oauth/custom |
| `auth_credentials` | BYTEA | NULL | Encrypted credentials |
| `command` | VARCHAR(200) | NULL | Executable command (STDIO) |
| `args` | JSONB | NULL | Command arguments (STDIO) |
| `env_vars` | JSONB | NULL | Environment variables (STDIO) |
| `working_dir` | VARCHAR(500) | NULL | Process working directory (STDIO) |
| `startup_timeout_ms` | INTEGER | DEFAULT 30000 | Process startup timeout (STDIO) |
| `input_schema` | JSONB | NOT NULL | JSON Schema for input |
| `output_schema` | JSONB | NULL | JSON Schema for output |
| `is_enabled` | BOOLEAN | DEFAULT true | Tool enabled |
| `is_validated` | BOOLEAN | DEFAULT false | Passed validation |
| `last_validated_at` | TIMESTAMPTZ | NULL | Last validation time |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update time |

Indexes:
- `idx_user_mcp_tools_user_id` ON (user_id)
- UNIQUE (user_id, name) - No duplicate tool names per user

### mcp_command_whitelist

Approved commands for process-based MCP servers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `command` | VARCHAR(100) | UNIQUE, NOT NULL | Command name |
| `description` | TEXT | NULL | Command description |
| `allowed_for_users` | BOOLEAN | DEFAULT true | Users can use this command |
| `created_by` | UUID | FK → users | Admin who added |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |

Indexes:
- `idx_mcp_command_whitelist_command` ON (command)

**Default Whitelisted Commands:**
| Command | Description |
|---------|-------------|
| `npx` | Node.js package runner |
| `node` | Node.js runtime |
| `python` | Python interpreter |
| `python3` | Python 3 interpreter |
| `uvx` | Python uv package runner |
| `deno` | Deno runtime |

### user_tool_configs

Per-user configuration overrides for tools.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | UUID | FK → users, NOT NULL | User reference |
| `tool_id` | UUID | NOT NULL | Tool ID (global or user) |
| `tool_type` | VARCHAR(10) | NOT NULL | 'global' or 'user' |
| `custom_config` | JSONB | NULL | Custom configuration |
| `is_favorite` | BOOLEAN | DEFAULT false | Favorite flag |
| `use_count` | INTEGER | DEFAULT 0 | Usage counter |
| `last_used_at` | TIMESTAMPTZ | NULL | Last usage time |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update time |

Indexes:
- UNIQUE (user_id, tool_id, tool_type)

### tool_shares

Sharing personal tools with other users.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `tool_id` | UUID | FK → user_mcp_tools | Shared tool |
| `owner_id` | UUID | FK → users, NOT NULL | Tool owner |
| `shared_with_id` | UUID | FK → users, NOT NULL | Recipient user |
| `permission` | VARCHAR(20) | DEFAULT 'use' | use/configure |
| `shared_at` | TIMESTAMPTZ | DEFAULT now() | Share timestamp |
| `expires_at` | TIMESTAMPTZ | NULL | Optional expiration |

Indexes:
- UNIQUE (tool_id, shared_with_id)

## 5.5 Chat Tables

### chat_threads

Chat conversation threads.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | UUID | FK → users, NOT NULL | Owner user |
| `folder_id` | UUID | FK → folders, NULL | Parent folder |
| `title` | VARCHAR(255) | NOT NULL | Thread title |
| `system_prompt` | TEXT | NULL | Custom system prompt |
| `model_override` | VARCHAR(50) | NULL | Model override |
| `temperature` | DECIMAL(3,2) | DEFAULT 0.7 | Temperature setting |
| `is_archived` | BOOLEAN | DEFAULT false | Archived flag |
| `is_pinned` | BOOLEAN | DEFAULT false | Pinned flag |
| `message_count` | INTEGER | DEFAULT 0 | Cached message count |
| `last_message_at` | TIMESTAMPTZ | NULL | Last message time |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update time |

Indexes:
- `idx_chat_threads_user_id` ON (user_id)
- `idx_chat_threads_folder_id` ON (folder_id)
- `idx_chat_threads_user_updated` ON (user_id, updated_at DESC)

### chat_messages

Individual messages within chat threads.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `thread_id` | UUID | FK → chat_threads, NOT NULL | Parent thread |
| `role` | VARCHAR(20) | NOT NULL | user/assistant/system/tool |
| `content` | TEXT | NOT NULL | Message content |
| `token_count` | INTEGER | NULL | Token count |
| `model_used` | VARCHAR(50) | NULL | LLM model used |
| `finish_reason` | VARCHAR(20) | NULL | stop/length/tool_calls |
| `parent_message_id` | UUID | FK → chat_messages, NULL | For branching |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |
| `metadata` | JSONB | NULL | Additional metadata |

Indexes:
- `idx_chat_messages_thread_id` ON (thread_id)
- `idx_chat_messages_thread_created` ON (thread_id, created_at)

### chat_context

Conversation context state for long conversations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `thread_id` | UUID | FK → chat_threads, UNIQUE | Thread reference |
| `context_window` | JSONB | NOT NULL | Current context messages |
| `total_tokens` | INTEGER | DEFAULT 0 | Total tokens in context |
| `summary` | TEXT | NULL | Conversation summary |
| `summary_up_to_message_id` | UUID | NULL | Last summarized message |
| `pinned_messages` | UUID[] | DEFAULT '{}' | Always-include messages |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update time |

### chat_tool_attachments

Tools attached to specific chat threads.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `thread_id` | UUID | FK → chat_threads, NOT NULL | Chat thread |
| `tool_id` | UUID | NOT NULL | Tool ID (global or user) |
| `tool_type` | VARCHAR(10) | NOT NULL | 'global' or 'user' |
| `attached_at` | TIMESTAMPTZ | DEFAULT now() | Attachment time |
| `attached_by` | UUID | FK → users | User who attached |

Indexes:
- UNIQUE (thread_id, tool_id, tool_type)
- `idx_chat_tool_attachments_thread_id` ON (thread_id)

### tool_calls

Audit log of MCP tool executions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `thread_id` | UUID | FK → chat_threads | Chat thread |
| `message_id` | UUID | FK → chat_messages | Triggering message |
| `user_id` | UUID | FK → users, NOT NULL | User who triggered |
| `tool_id` | UUID | NOT NULL | Tool ID |
| `tool_type` | VARCHAR(10) | NOT NULL | 'global' or 'user' |
| `tool_name` | VARCHAR(100) | NOT NULL | Tool name (denormalized) |
| `input` | JSONB | NOT NULL | Tool input |
| `output` | JSONB | NULL | Tool output |
| `status` | VARCHAR(20) | NOT NULL | pending/running/success/error |
| `error_message` | TEXT | NULL | Error details if failed |
| `duration_ms` | INTEGER | NULL | Execution duration |
| `tokens_used` | INTEGER | NULL | Tokens if applicable |
| `started_at` | TIMESTAMPTZ | DEFAULT now() | Start time |
| `completed_at` | TIMESTAMPTZ | NULL | Completion time |

Indexes:
- `idx_tool_calls_thread_id` ON (thread_id)
- `idx_tool_calls_user_id` ON (user_id)
- `idx_tool_calls_started_at` ON (started_at DESC)

## 5.6 Document Tables

### documents

Markdown documents.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | UUID | FK → users, NOT NULL | Owner user |
| `folder_id` | UUID | FK → folders, NULL | Parent folder |
| `title` | VARCHAR(255) | NOT NULL | Document title |
| `content` | TEXT | NOT NULL | Markdown content |
| `content_text` | TEXT | NULL | Plain text for search |
| `version` | INTEGER | DEFAULT 1 | Current version number |
| `word_count` | INTEGER | DEFAULT 0 | Cached word count |
| `is_archived` | BOOLEAN | DEFAULT false | Archived flag |
| `is_pinned` | BOOLEAN | DEFAULT false | Pinned flag |
| `is_template` | BOOLEAN | DEFAULT false | Template flag |
| `last_edited_at` | TIMESTAMPTZ | DEFAULT now() | Last edit time |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update time |

Indexes:
- `idx_documents_user_id` ON (user_id)
- `idx_documents_folder_id` ON (folder_id)
- `idx_documents_user_updated` ON (user_id, updated_at DESC)
- GIN index on content_text for full-text search

### document_versions

Document version history.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `document_id` | UUID | FK → documents, NOT NULL | Parent document |
| `version` | INTEGER | NOT NULL | Version number |
| `title` | VARCHAR(255) | NOT NULL | Title at this version |
| `content` | TEXT | NOT NULL | Content at this version |
| `word_count` | INTEGER | DEFAULT 0 | Word count |
| `change_summary` | VARCHAR(500) | NULL | Change description |
| `is_auto_save` | BOOLEAN | DEFAULT true | Auto vs manual save |
| `created_by` | UUID | FK → users | User who created |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |

Indexes:
- UNIQUE (document_id, version)
- `idx_document_versions_document_id` ON (document_id)

### document_links

Wiki-style links between documents.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `source_document_id` | UUID | FK → documents, NOT NULL | Linking document |
| `target_document_id` | UUID | FK → documents, NOT NULL | Linked document |
| `link_text` | VARCHAR(255) | NOT NULL | Display text |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |

Indexes:
- UNIQUE (source_document_id, target_document_id, link_text)
- `idx_document_links_source` ON (source_document_id)
- `idx_document_links_target` ON (target_document_id)

## 5.7 Comment Tables

### comment_threads

Comment threads anchored to document text ranges.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `document_id` | UUID | FK → documents, NOT NULL | Parent document |
| `user_id` | UUID | FK → users, NOT NULL | Thread creator |
| `anchor_start` | INTEGER | NOT NULL | Start character offset |
| `anchor_end` | INTEGER | NOT NULL | End character offset |
| `anchor_text` | TEXT | NOT NULL | Anchored text snapshot |
| `status` | VARCHAR(20) | DEFAULT 'open' | open/resolved |
| `resolved_by` | UUID | FK → users, NULL | User who resolved |
| `resolved_at` | TIMESTAMPTZ | NULL | Resolution time |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update time |

Indexes:
- `idx_comment_threads_document_id` ON (document_id)
- `idx_comment_threads_document_status` ON (document_id, status)

### comments

Individual comments within threads.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `thread_id` | UUID | FK → comment_threads, NOT NULL | Parent thread |
| `user_id` | UUID | FK → users, NOT NULL | Comment author |
| `content` | TEXT | NOT NULL | Comment content |
| `is_edited` | BOOLEAN | DEFAULT false | Edited flag |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update time |

Indexes:
- `idx_comments_thread_id` ON (thread_id)
- `idx_comments_thread_created` ON (thread_id, created_at)

### document_shares

Document sharing records for collaborative review.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `document_id` | UUID | FK → documents, CASCADE | Shared document |
| `owner_id` | UUID | FK → users, CASCADE | Document owner |
| `shared_with_id` | UUID | FK → users, CASCADE | Recipient user |
| `permission_level` | VARCHAR(20) | NOT NULL | read/comment/edit |
| `expires_at` | TIMESTAMPTZ | NULL | Optional expiration |
| `is_active` | BOOLEAN | DEFAULT true | Active status |
| `revoked_at` | TIMESTAMPTZ | NULL | Revocation timestamp |
| `revoked_by` | UUID | FK → users, NULL | User who revoked |
| `message` | TEXT | NULL | Optional share message |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | Last update time |

Indexes:
- `idx_document_shares_document_id` ON (document_id)
- `idx_document_shares_shared_with_id` ON (shared_with_id)
- UNIQUE (document_id, shared_with_id)

## 5.8 Attachment Tables

### attachments

File attachments for messages and documents. Processing is delegated to MMDI service.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | UUID | FK → users, NOT NULL | Uploader |
| `filename` | VARCHAR(255) | NOT NULL | Original filename |
| `content_type` | VARCHAR(100) | NOT NULL | MIME type |
| `file_size` | BIGINT | NOT NULL | Size in bytes |
| `checksum_sha256` | VARCHAR(64) | NOT NULL | File hash |
| `mmdi_job_id` | UUID | NULL | MMDI processing job ID |
| `mmdi_status` | VARCHAR(20) | DEFAULT 'pending' | MMDI job status |
| `mmdi_file_location` | VARCHAR(500) | NULL | MMDI storage URI |
| `mmdi_content_hash` | VARCHAR(64) | NULL | SHA256 of extracted content |
| `mmdi_quality_level` | INTEGER | DEFAULT 2 | MMDI quality level used |
| `extracted_content` | TEXT | NULL | Cached extracted markdown |
| `is_processed` | BOOLEAN | DEFAULT false | MMDI processing complete |
| `processing_error` | TEXT | NULL | Error message if failed |
| `attached_to_type` | VARCHAR(20) | NOT NULL | 'message' or 'document' |
| `attached_to_id` | UUID | NOT NULL | Message or document ID |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Upload time |
| `processed_at` | TIMESTAMPTZ | NULL | MMDI completion time |

Indexes:
- `idx_attachments_user_id` ON (user_id)
- `idx_attachments_attached_to` ON (attached_to_type, attached_to_id)
- `idx_attachments_mmdi_job_id` ON (mmdi_job_id) WHERE mmdi_job_id IS NOT NULL
- `idx_attachments_mmdi_status` ON (mmdi_status) WHERE mmdi_status IN ('pending', 'started')

### ingestion_jobs

Background job tracking for post-MMDI processing (embeddings, etc.).

Note: Document extraction (PDF, DOCX, etc.) is handled by MMDI service.
This table tracks Bridge Platform's internal jobs like embedding generation.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `attachment_id` | UUID | FK → attachments, NOT NULL | Attachment reference |
| `job_type` | VARCHAR(50) | NOT NULL | embedding/export/index |
| `status` | VARCHAR(20) | NOT NULL | pending/running/success/failed |
| `progress` | INTEGER | DEFAULT 0 | Progress percentage |
| `error_message` | TEXT | NULL | Error details |
| `attempts` | INTEGER | DEFAULT 0 | Retry count |
| `max_attempts` | INTEGER | DEFAULT 3 | Max retries |
| `mmdi_job_id` | UUID | NULL | Reference to MMDI job if applicable |
| `started_at` | TIMESTAMPTZ | NULL | Start time |
| `completed_at` | TIMESTAMPTZ | NULL | Completion time |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |

Indexes:
- `idx_ingestion_jobs_attachment_id` ON (attachment_id)
- `idx_ingestion_jobs_status` ON (status) WHERE status IN ('pending', 'running')
- `idx_ingestion_jobs_mmdi_job_id` ON (mmdi_job_id) WHERE mmdi_job_id IS NOT NULL

## 5.9 RAG Tables

### embedding_chunks

Vector embeddings for RAG retrieval.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | UUID | FK → users, NOT NULL | Owner |
| `source_type` | VARCHAR(20) | NOT NULL | 'document' or 'attachment' |
| `source_id` | UUID | NOT NULL | Document or attachment ID |
| `chunk_index` | INTEGER | NOT NULL | Chunk position |
| `content` | TEXT | NOT NULL | Chunk text content |
| `token_count` | INTEGER | NOT NULL | Token count |
| `embedding` | vector(1536) | NOT NULL | Embedding vector |
| `metadata` | JSONB | NULL | Additional metadata |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Creation time |

Indexes:
- `idx_embedding_chunks_user_id` ON (user_id)
- `idx_embedding_chunks_source` ON (source_type, source_id)
- HNSW index on embedding for vector similarity search:
  `CREATE INDEX idx_embedding_chunks_vector ON embedding_chunks USING hnsw (embedding vector_cosine_ops)`

## 5.10 Session & Audit Tables

Note: Session and token management is handled by Amini0. Bridge Platform only
tracks local audit information.

### user_sessions (local tracking only)

Tracks user sessions for audit and analytics (tokens managed by Amini0).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | UUID | FK → users, NOT NULL | User reference |
| `amini0_session_id` | UUID | NULL | Amini0 session ID (if available) |
| `device_info` | VARCHAR(255) | NULL | Device identifier |
| `ip_address` | INET | NULL | IP address |
| `user_agent` | VARCHAR(500) | NULL | Browser user agent |
| `first_seen_at` | TIMESTAMPTZ | DEFAULT now() | First activity |
| `last_seen_at` | TIMESTAMPTZ | DEFAULT now() | Last activity |

Indexes:
- `idx_user_sessions_user_id` ON (user_id)
- `idx_user_sessions_last_seen` ON (last_seen_at DESC)

### audit_logs

System audit trail.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | UUID | FK → users, NULL | Acting user |
| `action` | VARCHAR(100) | NOT NULL | Action performed |
| `resource_type` | VARCHAR(50) | NOT NULL | Affected resource type |
| `resource_id` | UUID | NULL | Affected resource ID |
| `details` | JSONB | NULL | Action details |
| `ip_address` | INET | NULL | Client IP |
| `user_agent` | VARCHAR(500) | NULL | Client user agent |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Action time |

Indexes:
- `idx_audit_logs_user_id` ON (user_id)
- `idx_audit_logs_resource` ON (resource_type, resource_id)
- `idx_audit_logs_created_at` ON (created_at DESC)

Partitioning: Consider partitioning by created_at (monthly) for large deployments.

## 5.11 Entity Relationship Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                           USERS & AUTH                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────┐      ┌──────────────────┐      ┌─────────────────────┐  │
│  │  users  │──1:N─│ wallet_addresses │      │ nft_permission_cache│  │
│  └────┬────┘      └──────────────────┘      └─────────────────────┘  │
│       │                                                               │
│       ├──1:1── user_settings                                          │
│       │                                                               │
│       └──M:N── groups ──M:N── policies                                │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                         CONTENT & FOLDERS                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  users ──1:N── folders (self-referencing for hierarchy)               │
│            │                                                          │
│            ├──1:N── chat_threads ──1:N── chat_messages                │
│            │              │                                           │
│            │              ├──1:1── chat_context                       │
│            │              └──1:N── chat_tool_attachments              │
│            │                                                          │
│            └──1:N── documents ──1:N── document_versions               │
│                          │                                            │
│                          ├──M:N── document_links (self-ref)           │
│                          ├──1:N── document_shares ──N:1── users       │
│                          └──1:N── comment_threads ──1:N── comments    │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                            MCP TOOLS                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  mcp_tools_global (admin-managed)                                     │
│                                                                       │
│  users ──1:N── user_mcp_tools ──1:N── tool_shares                     │
│            │                                                          │
│            └──1:N── user_tool_configs                                 │
│                                                                       │
│  chat_threads ──1:N── tool_calls (audit)                              │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                        ATTACHMENTS & RAG                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  attachments ──1:N── ingestion_jobs                                   │
│       │                                                               │
│       └── (documents | chat_messages)                                 │
│                                                                       │
│  embedding_chunks ── (documents | attachments)                        │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

------------------------------------------------------------------------

# 6. Frontend Architecture (Svelte 5)

## 6.1 Architectural Pattern: MVVM (Mandatory)

The frontend must follow the MVVM (Model-View-ViewModel) architecture
pattern, using Tailwind CSS for styling.

View: - Pure Svelte components responsible only for rendering and UI
interaction. - No business logic.

ViewModel: - Presentation logic - API calls - SSE streaming handling -
Tool attachment state management - Folder tree management - Markdown
document state handling - Comment lifecycle handling

Model: - TypeScript interfaces - DTO contracts - Shared schemas

The View must not directly call API services. All API interaction must
go through ViewModels.

## 6.2 Styling with Tailwind CSS

The frontend uses Tailwind CSS as the primary styling solution.

Styling Guidelines:

-   Use Tailwind utility classes directly in Svelte components
-   Avoid custom CSS unless absolutely necessary
-   Use Tailwind's design system for consistency (spacing, colors, typography)
-   Configure theme extensions in `tailwind.config.js` for brand colors
-   Use `@apply` sparingly, prefer utility classes in markup
-   Leverage Tailwind's responsive prefixes (`sm:`, `md:`, `lg:`, `xl:`)
-   Use Tailwind's dark mode support (`dark:` prefix)

Component Styling:

-   Keep styles co-located with components (utility classes in markup)
-   Use Tailwind's component patterns for reusable styles
-   Maintain consistent spacing and sizing across the application

## 6.3 MCP-Driven Functionality Model

The frontend follows a thin-client approach where new features and capabilities
are delivered through MCP tools rather than frontend code changes.

Core Principle:

-   The frontend UI remains stable and minimal
-   New functionality is introduced via MCP tools
-   The UI dynamically renders tool outputs and interactions
-   Frontend updates are primarily for UX improvements, not new features

How it works:

-   MCP tools define their own input schemas and output formats
-   The frontend provides generic renderers for common output types
-   Tool-specific UI components are loaded dynamically when needed
-   ViewModels orchestrate tool invocation and response handling

Benefits:

-   Faster feature delivery (no frontend deployment required)
-   Users can extend functionality by adding their own MCP tools
-   Reduced frontend complexity and maintenance burden
-   Consistent user experience across all tools
-   A/B testing of features via tool variants

Frontend responsibilities (minimal scope):

-   Core chat interface and message rendering
-   Folder navigation and document editing
-   Tool attachment/detachment UI
-   Generic tool output renderers (text, tables, charts, forms)
-   Authentication and wallet connection

MCP tool responsibilities (feature delivery):

-   Domain-specific logic and processing
-   Custom data transformations
-   External integrations and API calls
-   Specialized output formats and visualizations
-   New capabilities without frontend changes

------------------------------------------------------------------------

# 7. Background Worker Responsibilities

-   PDF ingestion
-   CSV parsing
-   OCR
-   Embedding generation
-   Tool execution orchestration (async)
-   Document export

Redis recommended for job queue.

------------------------------------------------------------------------

# 8. Quality Engineering Requirements

Mandatory:

-   Test-Driven Development (TDD)
-   Behavior-Driven Development (BDD)
-   Minimum 70% code coverage

TDD applies to domain logic, folder operations, tool attachment, comment
resolution, and policy enforcement.

BDD must define Gherkin scenarios for critical flows including Chat +
MCP, Document Commenting, and Folder Management.

CI must fail if coverage drops below 70%.

Recommended Tools:

Backend: - pytest - pytest-cov - pytest-bdd

Frontend: - Vitest - Playwright

------------------------------------------------------------------------

# 9. Non-Functional Requirements

-   Stateless API
-   Async FastAPI endpoints
-   Horizontal scalability
-   Secure JWT authentication with wallet signature verification
-   NFT-based permission extraction from Aminichain
-   Role-based tool access control (derived from NFT attributes)
-   Full audit trail for tool calls
-   Structured logging
-   Health checks
-   Containerized reproducibility
-   Web3 integration for blockchain queries

------------------------------------------------------------------------

# 10. Security

## 10.1 Authentication Security (Amini0 Delegated)

Authentication is delegated to Amini0 Auth Service. Bridge Platform validates Amini0-issued JWTs.

Amini0 Handles (see Amini0 TRD for details):
-   Email/password authentication with Argon2 hashing
-   OAuth integration (Google, Microsoft)
-   Wallet authentication (SIWE - Sign-In with Ethereum)
-   JWT token generation (HS256 or RS256)
-   Session management and revocation
-   NFT Identity minting and IAM

Bridge Platform JWT Validation:
-   Validates JWTs using Amini0's public key (RS256) or shared secret (HS256)
-   Accepts short-lived access tokens (15 minutes default)
-   Extracts user_id, email, wallet_address, permissions from claims
-   Rejects expired or invalid tokens with 401 response
-   Caches user permissions from JWT claims

Token Flow:
1. User authenticates with Amini0 (any supported method)
2. Amini0 returns access_token + refresh_token
3. Frontend stores tokens securely (httpOnly cookies recommended)
4. Frontend sends access_token to Bridge Platform API
5. Bridge Platform validates token and extracts user context
6. Frontend refreshes tokens directly with Amini0

## 10.2 Input Validation & Sanitization

Backend:
-   Pydantic models for all request validation
-   SQL injection prevention via SQLAlchemy ORM
-   File upload validation (type, size, content inspection)
-   Markdown sanitization before storage
-   URL validation for MCP tool endpoints

Frontend:
-   Input sanitization before display
-   CSP (Content Security Policy) headers
-   XSS prevention via Svelte's built-in escaping

## 10.3 OWASP Top 10 Mitigations

| Risk | Mitigation |
|------|------------|
| Injection | Parameterized queries, ORM usage |
| Broken Auth | Wallet signatures, JWT rotation |
| Sensitive Data | Encryption at rest, TLS in transit |
| XXE | Disable XML parsing, JSON-only API |
| Broken Access | NFT-based permissions, middleware checks |
| Security Misconfig | Hardened Docker images, env validation |
| XSS | CSP headers, output encoding |
| Insecure Deserialization | Pydantic validation, no pickle |
| Vulnerable Components | Dependabot, regular updates |
| Insufficient Logging | Structured logging, audit trail |

## 10.4 Data Protection

Encryption at Rest:
-   Database: PostgreSQL with encryption (via disk encryption)
-   S3: Server-side encryption enabled
-   Sensitive fields: AES-256 encryption for tool credentials

Encryption in Transit:
-   TLS 1.3 for all connections
-   HTTPS enforced (HSTS headers)
-   Secure WebSocket (WSS)

Data Retention:
-   Chat messages: Retained until user deletion
-   Audit logs: 90 days retention
-   Deleted content: Soft delete, hard delete after 30 days
-   Session data: Cleared on logout

## 10.5 Rate Limiting

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Auth endpoints | 10 requests | 1 minute |
| Chat messages | 30 requests | 1 minute |
| File uploads | 10 requests | 1 minute |
| Tool executions | Based on NFT tier | 1 minute |
| Search queries | 60 requests | 1 minute |
| General API | 300 requests | 1 minute |

Implementation:
-   Redis-based rate limiting
-   Per-user and per-IP limits
-   Rate limit headers in responses
-   Graceful degradation (429 Too Many Requests)

## 10.6 MCP Tool Security

### HTTP Transport Security

-   Tool endpoints validated against allowlist (admin-configured)
-   User tool endpoints restricted by NFT permissions
-   Tool credentials encrypted with per-user keys
-   HTTPS required for production endpoints
-   Tool responses sanitized before display
-   Tool call audit logging (who, what, when, result)

### STDIO Transport Security (Process-Based MCP)

-   **Command Whitelist**: Only approved commands can be used (npx, node, python, etc.)
-   **Whitelist Management**: Admins control which commands are allowed
-   **User Restrictions**: `allowed_for_users` flag controls user access to commands
-   **Argument Validation**: Command arguments sanitized to prevent injection
-   **Environment Variable Isolation**: Each process runs with controlled environment
-   **Timeout Enforcement**: Processes killed if they exceed startup or execution timeout
-   **Process Isolation**: Each tool runs in separate process space
-   **Resource Limits**: Future: cgroups/containers for resource limiting
-   **Session Cleanup**: Processes properly terminated on tool detach or session end

### Common Security Measures

-   Tool execution sandboxed with configurable timeouts
-   Rate limiting per user (NFT-based quotas)
-   All tool calls logged with full audit trail
-   Tool validation required before first use

------------------------------------------------------------------------

# 11. Project Directory Structure

## 11.1 Backend Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry
│   ├── config.py                  # Configuration management
│   │
│   ├── domain/                    # Domain layer (pure business logic)
│   │   ├── entities/              # Domain entities
│   │   │   ├── user.py
│   │   │   ├── chat.py
│   │   │   ├── document.py
│   │   │   ├── folder.py
│   │   │   ├── tool.py
│   │   │   └── comment.py
│   │   ├── value_objects/         # Value objects
│   │   │   ├── wallet_address.py
│   │   │   ├── permission.py
│   │   │   ├── tool_config.py
│   │   │   └── mcp_config.py       # MCP transport configuration
│   │   ├── exceptions.py          # Domain exceptions
│   │   └── events.py              # Domain events
│   │
│   ├── application/               # Application layer (use cases)
│   │   ├── use_cases/
│   │   │   ├── auth/
│   │   │   ├── chat/
│   │   │   ├── document/
│   │   │   ├── folder/
│   │   │   ├── tool/
│   │   │   ├── attachment/        # File upload via MMDI
│   │   │   └── rag/
│   │   ├── interfaces/            # Port interfaces
│   │   │   ├── repositories.py
│   │   │   ├── llm_provider.py
│   │   │   ├── storage.py
│   │   │   ├── blockchain.py
│   │   │   └── document_ingestion.py  # MMDI port interface
│   │   └── dto/                   # Data transfer objects
│   │
│   ├── infrastructure/            # Infrastructure layer (adapters)
│   │   ├── database/
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   ├── repositories/      # Repository implementations
│   │   │   └── migrations/        # Alembic migrations
│   │   ├── llm/
│   │   │   ├── openai_adapter.py
│   │   │   └── amini_adapter.py
│   │   ├── storage/
│   │   │   └── s3_adapter.py
│   │   ├── blockchain/
│   │   │   └── aminichain_adapter.py
│   │   ├── mmdi/
│   │   │   ├── mmdi_adapter.py    # MMDI REST API client
│   │   │   └── webhook_handler.py # MMDI webhook processing
│   │   ├── amini_rag/
│   │   │   ├── rag_adapter.py     # Amini RAG REST/MCP client
│   │   │   └── rag_tool.py        # MCP tool wrapper for RAG
│   │   ├── mcp/
│   │   │   ├── tool_executor.py
│   │   │   ├── mcp_process_client.py  # STDIO MCP client
│   │   │   └── mcp_router.py          # Transport routing
│   │   └── queue/
│   │       └── redis_queue.py
│   │
│   ├── api/                       # API layer (FastAPI routes)
│   │   ├── dependencies.py        # Dependency injection
│   │   ├── middleware/
│   │   │   ├── auth.py
│   │   │   ├── rate_limit.py
│   │   │   └── logging.py
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── chats.py
│   │   │   ├── documents.py
│   │   │   ├── folders.py
│   │   │   ├── tools.py
│   │   │   ├── attachments.py     # File uploads (proxied to MMDI)
│   │   │   ├── webhooks.py        # MMDI webhook callbacks
│   │   │   ├── assistant.py       # AI Writing Assistant
│   │   │   └── admin.py
│   │   └── schemas/               # Pydantic request/response schemas
│   │
│   └── workers/                   # Background workers
│       ├── ingestion.py
│       ├── embedding.py
│       └── export.py
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   ├── integration/
│   ├── bdd/
│   │   └── features/              # Gherkin feature files
│   └── conftest.py
│
├── alembic/                       # Database migrations
├── scripts/                       # Utility scripts
├── Dockerfile
├── docker-compose.yml             # Production compose
├── docker-compose.dev.yml         # Local development (DB, Redis, MinIO)
├── pyproject.toml                 # Python project config (uv)
├── justfile                       # Task runner commands
├── .env.example
└── README.md
```

## 11.2 Frontend Structure

```
frontend/
├── src/
│   ├── lib/
│   │   ├── components/            # View layer (Svelte components)
│   │   │   ├── chat/
│   │   │   │   ├── ChatThread.svelte
│   │   │   │   ├── MessageList.svelte
│   │   │   │   ├── MessageInput.svelte
│   │   │   │   ├── ToolCallDisplay.svelte
│   │   │   │   └── SaveAsDocumentModal.svelte  # Save chat to document
│   │   │   ├── document/
│   │   │   │   ├── Editor.svelte
│   │   │   │   ├── VersionHistory.svelte
│   │   │   │   ├── CommentThread.svelte
│   │   │   │   ├── CommentSidebar.svelte
│   │   │   │   ├── ShareDocumentModal.svelte    # Document sharing modal
│   │   │   │   ├── SharedDocumentsList.svelte   # Shared with me list
│   │   │   │   └── WritingAssistant.svelte      # AI Assistant Panel
│   │   │   ├── folder/
│   │   │   │   ├── FolderTree.svelte
│   │   │   │   └── FolderItem.svelte
│   │   │   ├── tools/
│   │   │   │   ├── ToolCatalog.svelte
│   │   │   │   ├── ToolConfig.svelte
│   │   │   │   └── ToolOutputRenderer.svelte
│   │   │   ├── auth/
│   │   │   │   └── WalletConnect.svelte
│   │   │   └── common/
│   │   │       ├── Button.svelte
│   │   │       ├── Modal.svelte
│   │   │       └── Loading.svelte
│   │   │
│   │   ├── viewmodels/            # ViewModel layer
│   │   │   ├── auth.svelte.ts
│   │   │   ├── chat.svelte.ts
│   │   │   ├── document.svelte.ts
│   │   │   ├── document-share.svelte.ts  # Document sharing viewmodels
│   │   │   ├── folder.svelte.ts
│   │   │   ├── tools.svelte.ts
│   │   │   ├── writing-assistant.svelte.ts  # AI Writing Assistant
│   │   │   └── settings.svelte.ts
│   │   │
│   │   ├── models/                # Model layer (types & DTOs)
│   │   │   ├── user.ts
│   │   │   ├── chat.ts
│   │   │   ├── document.ts
│   │   │   ├── document-share.ts  # Document sharing models
│   │   │   ├── folder.ts
│   │   │   ├── tool.ts
│   │   │   └── api.ts
│   │   │
│   │   ├── services/              # API service layer
│   │   │   ├── api.ts             # Base API client
│   │   │   ├── auth.ts
│   │   │   ├── chat.ts
│   │   │   ├── document.ts
│   │   │   ├── document-share.ts  # Document sharing service
│   │   │   ├── folder.ts
│   │   │   ├── tools.ts
│   │   │   └── sse.ts             # SSE streaming client
│   │   │
│   │   ├── stores/                # Svelte stores (global state)
│   │   │   ├── auth.ts
│   │   │   └── ui.ts
│   │   │
│   │   └── utils/                 # Utility functions
│   │       ├── markdown.ts
│   │       ├── wallet.ts
│   │       └── formatting.ts
│   │
│   ├── routes/                    # SvelteKit routes
│   │   ├── +layout.svelte
│   │   ├── +page.svelte
│   │   ├── chat/
│   │   │   └── [id]/+page.svelte
│   │   ├── document/
│   │   │   └── [id]/+page.svelte
│   │   ├── shared/                    # Shared documents routes
│   │   │   ├── +page.svelte           # Documents shared with me
│   │   │   └── [documentId]/+page.svelte  # View shared document
│   │   ├── tools/
│   │   │   └── +page.svelte
│   │   └── settings/
│   │       └── +page.svelte
│   │
│   ├── app.html
│   ├── app.css
│   └── hooks.server.ts
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/                       # Playwright tests
│
├── static/
├── svelte.config.js
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
├── package.json
├── .env.example
└── README.md
```

## 11.3 Local Development Workflow

### Prerequisites

-   Python 3.11+
-   Node.js 20+
-   Docker & Docker Compose
-   [uv](https://github.com/astral-sh/uv) - `curl -LsSf https://astral.sh/uv/install.sh | sh`
-   [just](https://github.com/casey/just) - `cargo install just` or `brew install just`

### Justfile Commands

The project uses `just` as the task runner. Run `just` or `just --list` to see all available commands.

#### Infrastructure Commands

| Command | Description |
|---------|-------------|
| `just up` | Start all local infrastructure (PostgreSQL, Redis, MinIO) |
| `just down` | Stop all local infrastructure |
| `just logs` | View infrastructure logs |
| `just db-shell` | Open PostgreSQL shell |
| `just redis-cli` | Open Redis CLI |
| `just clean` | Stop infrastructure and remove volumes |

#### Backend Commands

| Command | Description |
|---------|-------------|
| `just install` | Install all dependencies (backend + frontend) |
| `just install-backend` | Install backend dependencies with uv |
| `just dev` | Start backend development server (uvicorn --reload) |
| `just migrate` | Run database migrations (alembic upgrade head) |
| `just migrate-create NAME` | Create new migration |
| `just migrate-down` | Rollback last migration |
| `just shell` | Open Python shell with app context |

#### Testing Commands

| Command | Description |
|---------|-------------|
| `just test` | Run all tests (backend + frontend) |
| `just test-backend` | Run backend tests with pytest |
| `just test-unit` | Run backend unit tests only |
| `just test-integration` | Run backend integration tests |
| `just test-bdd` | Run BDD tests (Gherkin scenarios) |
| `just test-cov` | Run tests with coverage report |
| `just test-frontend` | Run frontend tests with Vitest |
| `just test-e2e` | Run Playwright E2E tests |

#### Code Quality Commands

| Command | Description |
|---------|-------------|
| `just lint` | Lint all code (Ruff + ESLint) |
| `just lint-fix` | Auto-fix lint issues |
| `just format` | Format all code (Ruff + Prettier) |
| `just typecheck` | Run type checking (mypy + tsc) |
| `just check` | Run all checks (lint, format, typecheck, test) |

#### Frontend Commands

| Command | Description |
|---------|-------------|
| `just install-frontend` | Install frontend dependencies |
| `just dev-frontend` | Start frontend development server |
| `just build-frontend` | Build frontend for production |

#### Docker Commands

| Command | Description |
|---------|-------------|
| `just docker-build` | Build all Docker images |
| `just docker-up` | Start full stack in Docker |
| `just docker-down` | Stop Docker stack |
| `just docker-logs` | View Docker logs |

### Example Justfile

```justfile
# Default recipe (show help)
default:
    @just --list

# ─────────────────────────────────────────────────────────────────────────────
# Infrastructure
# ─────────────────────────────────────────────────────────────────────────────

# Start local infrastructure (PostgreSQL, Redis, MinIO)
up:
    docker compose -f docker-compose.dev.yml up -d
    @echo "Waiting for PostgreSQL..."
    @sleep 3
    @echo "Infrastructure ready!"

# Stop local infrastructure
down:
    docker compose -f docker-compose.dev.yml down

# View infrastructure logs
logs *ARGS:
    docker compose -f docker-compose.dev.yml logs {{ARGS}}

# Stop infrastructure and remove volumes
clean:
    docker compose -f docker-compose.dev.yml down -v

# Open PostgreSQL shell
db-shell:
    docker compose -f docker-compose.dev.yml exec db psql -U bridge -d bridge

# Open Redis CLI
redis-cli:
    docker compose -f docker-compose.dev.yml exec redis redis-cli

# ─────────────────────────────────────────────────────────────────────────────
# Backend
# ─────────────────────────────────────────────────────────────────────────────

# Install all dependencies
install: install-backend install-frontend

# Install backend dependencies
install-backend:
    cd backend && uv sync

# Start backend development server
dev:
    cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run database migrations
migrate:
    cd backend && uv run alembic upgrade head

# Create new migration
migrate-create NAME:
    cd backend && uv run alembic revision --autogenerate -m "{{NAME}}"

# Rollback last migration
migrate-down:
    cd backend && uv run alembic downgrade -1

# Open Python shell with app context
shell:
    cd backend && uv run python -i -c "from app.main import app; print('App context loaded')"

# ─────────────────────────────────────────────────────────────────────────────
# Testing
# ─────────────────────────────────────────────────────────────────────────────

# Run all tests
test: test-backend test-frontend

# Run backend tests
test-backend:
    cd backend && uv run pytest

# Run backend unit tests
test-unit:
    cd backend && uv run pytest tests/unit/

# Run backend integration tests
test-integration:
    cd backend && uv run pytest tests/integration/

# Run BDD tests
test-bdd:
    cd backend && uv run pytest tests/bdd/

# Run tests with coverage
test-cov:
    cd backend && uv run pytest --cov=app --cov-report=term-missing --cov-report=html

# Run frontend tests
test-frontend:
    cd frontend && npm run test

# Run E2E tests
test-e2e:
    cd frontend && npm run test:e2e

# ─────────────────────────────────────────────────────────────────────────────
# Code Quality
# ─────────────────────────────────────────────────────────────────────────────

# Lint all code
lint:
    cd backend && uv run ruff check .
    cd frontend && npm run lint

# Auto-fix lint issues
lint-fix:
    cd backend && uv run ruff check --fix .
    cd frontend && npm run lint:fix

# Format all code
format:
    cd backend && uv run ruff format .
    cd frontend && npm run format

# Run type checking
typecheck:
    cd backend && uv run mypy app
    cd frontend && npm run typecheck

# Run all checks
check: lint typecheck test

# ─────────────────────────────────────────────────────────────────────────────
# Frontend
# ─────────────────────────────────────────────────────────────────────────────

# Install frontend dependencies
install-frontend:
    cd frontend && npm install

# Start frontend dev server
dev-frontend:
    cd frontend && npm run dev

# Build frontend for production
build-frontend:
    cd frontend && npm run build

# ─────────────────────────────────────────────────────────────────────────────
# Docker
# ─────────────────────────────────────────────────────────────────────────────

# Build all Docker images
docker-build:
    docker compose build

# Start full stack in Docker
docker-up:
    docker compose up -d

# Stop Docker stack
docker-down:
    docker compose down

# View Docker logs
docker-logs *ARGS:
    docker compose logs {{ARGS}}

# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

# Generate OpenAPI schema
openapi:
    cd backend && uv run python -c "from app.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > openapi.json

# Seed database with test data
seed:
    cd backend && uv run python scripts/seed_data.py

# Reset database (drop all, recreate, migrate, seed)
db-reset:
    docker compose -f docker-compose.dev.yml down -v
    docker compose -f docker-compose.dev.yml up -d db
    @sleep 3
    just migrate
    just seed
```

### docker-compose.dev.yml

Local development infrastructure (database, cache, storage):

```yaml
version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: bridge
      POSTGRES_PASSWORD: bridge_dev
      POSTGRES_DB: bridge
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bridge"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### Quick Start

```bash
# 1. Clone and enter directory
git clone https://github.com/aminitech/bridge_system.git
cd bridge_system

# 2. Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Start infrastructure
just up

# 4. Install dependencies
just install

# 5. Run migrations
just migrate

# 6. Start development servers (in separate terminals)
just dev           # Backend on :8000
just dev-frontend  # Frontend on :3000

# 7. Run tests
just test
```

------------------------------------------------------------------------

# 12. Deployment Architecture

## 12.1 Docker Compose Services

```yaml
services:
  # API Server
  api:
    build: ./backend
    replicas: 2
    depends_on: [db, redis]
    environment: [from .env]
    healthcheck: /health

  # Background Worker
  worker:
    build: ./backend
    command: worker
    replicas: 2
    depends_on: [db, redis]

  # Frontend (SSR + Static)
  frontend:
    build: ./frontend
    depends_on: [api]

  # PostgreSQL Database
  db:
    image: postgres:16
    volumes: [postgres_data]

  # Redis (Queue + Cache)
  redis:
    image: redis:7-alpine
    volumes: [redis_data]

  # MinIO (S3-compatible storage)
  minio:
    image: minio/minio
    volumes: [minio_data]

  # Nginx (Reverse Proxy)
  nginx:
    image: nginx:alpine
    ports: [80, 443]
    depends_on: [api, frontend]
```

## 12.2 Service Topology

```
                              ┌─────────────┐     ┌─────────────┐
                              │   Amini0    │     │    MMDI     │
                              │ (External)  │     │  (External) │
                              └──────┬──────┘     └──────┬──────┘
                                     │                   │
                    ┌─────────────┐  │                   │
                    │   Nginx     │  │                   │
                    │   (Proxy)   │  │                   │
                    └──────┬──────┘  │                   │
                           │         │                   │
           ┌───────────────┼─────────┼───────────────┐   │
           │               │         │               │   │
           ▼               ▼         │               ▼   │
    ┌─────────────┐ ┌─────────────┐  │        ┌─────────────┐
    │  Frontend   │ │  API (x2)   │──┼────────│  API SSE    │
    │  (SvelteKit)│◄┼─(FastAPI)───┼──┼───────▶│  Streaming  │
    └──────┬──────┘ └──────┬──────┘  │        └──────┬──────┘
           │               │         │               │
           │               │ JWT     │               │
           │               │ Validation              │
           └───────────────┴─────────┴───────────────┘
                           │                   │
           ┌───────────────┼───────────────┐   │
           │               │               │   │ File Upload
           ▼               ▼               ▼   │ & Content
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │  PostgreSQL │ │    Redis    │ │    MinIO    │
    │  (pgvector) │ │   (Queue)   │ │    (S3)     │
    └─────────────┘ └──────┬──────┘ └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Worker    │
                    │   (x2)      │
                    └─────────────┘

External Services:
- Amini0 Auth Service: Authentication, JWT tokens, IAM
- Aminichain RPC: Blockchain queries (via Amini0)
- MMDI Service: File upload, document processing, markdown extraction
- Amini RAG Service (optional): Knowledge graph RAG queries via MCP
```

## 12.3 Coolify Deployment

Coolify Configuration:
-   Project type: Docker Compose
-   Git repository auto-deploy on push to main
-   Environment variables managed in Coolify dashboard
-   SSL certificates via Let's Encrypt (automatic)
-   Health checks enabled for all services

Resource Allocation (MVP):
-   API: 512MB RAM, 0.5 CPU per instance
-   Worker: 1GB RAM, 0.5 CPU per instance
-   Frontend: 256MB RAM, 0.25 CPU
-   PostgreSQL: 1GB RAM, 0.5 CPU
-   Redis: 256MB RAM, 0.25 CPU
-   MinIO: 512MB RAM, 0.25 CPU

## 12.4 Scaling Strategy

Horizontal Scaling:
-   API servers: Scale based on request rate
-   Workers: Scale based on queue depth
-   Frontend: Single instance (stateless)

Vertical Scaling:
-   PostgreSQL: Increase resources for heavy queries
-   Redis: Increase memory for larger queues

Future Scaling:
-   Database read replicas
-   Redis cluster for high availability
-   CDN for static assets

------------------------------------------------------------------------

# 13. CI/CD Pipeline

## 13.1 Pipeline Stages

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│  Lint   │──▶│  Test   │──▶│  Build  │──▶│  Push   │──▶│ Deploy  │
└─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
```

## 13.2 GitHub Actions Workflow

```yaml
# Triggered on: push to main, pull requests
jobs:
  lint:
    - Backend: ruff, mypy
    - Frontend: eslint, prettier, svelte-check

  test:
    - Backend: pytest --cov (requires ≥70%)
    - Frontend: vitest --coverage
    - BDD: pytest-bdd (Gherkin scenarios)
    - E2E: playwright (critical paths)

  build:
    - Backend: Docker image build
    - Frontend: SvelteKit build + Docker image

  push:
    - Push images to container registry
    - Tag with commit SHA and 'latest'

  deploy:
    - Trigger Coolify webhook
    - Run database migrations
    - Health check verification
```

## 13.3 Quality Gates

Pull Request Checks (must pass):
-   All linters pass
-   All tests pass
-   Code coverage ≥ 70%
-   No security vulnerabilities (Dependabot)
-   Docker build succeeds

Merge Requirements:
-   At least 1 approval
-   All checks passing
-   Branch up to date with main

## 13.4 Deployment Environments

| Environment | Trigger | URL |
|-------------|---------|-----|
| Development | Push to feature/* | dev.bridge.amini.io |
| Staging | Push to main | staging.bridge.amini.io |
| Production | Manual approval | bridge.amini.io |

------------------------------------------------------------------------

# 14. Monitoring & Observability

## 14.1 Logging

Structured Logging Format:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "api",
  "request_id": "req_abc123",
  "user_id": "user_456",
  "message": "Chat message sent",
  "context": {
    "chat_id": "chat_789",
    "tool_count": 2
  }
}
```

Log Levels:
-   ERROR: Failures requiring attention
-   WARN: Unexpected but handled situations
-   INFO: Significant business events
-   DEBUG: Detailed debugging (dev only)

Log Aggregation:
-   Coolify built-in log viewer
-   Optional: Forward to external service (Loki, CloudWatch)

## 14.2 Metrics

Application Metrics:
-   Request rate (by endpoint)
-   Response time (p50, p95, p99)
-   Error rate (by error code)
-   Active users (concurrent sessions)
-   Chat messages per minute
-   Tool executions per minute
-   LLM token usage

Infrastructure Metrics:
-   CPU utilization per service
-   Memory usage per service
-   Database connections
-   Redis queue depth
-   S3 storage usage

## 14.3 Health Checks

Endpoints:
-   `GET /health` - Basic liveness check
-   `GET /health/ready` - Readiness (includes dependencies)

Readiness Checks:
-   Database connection
-   Redis connection
-   S3 connectivity
-   Amini0 Auth Service reachability
-   MMDI Service reachability (`/system/status`)
-   LLM provider reachability
-   Aminichain RPC reachability (via Amini0)
-   Amini RAG Service reachability (if enabled, `/health`)

## 14.4 Alerting

Critical Alerts (immediate):
-   Service down (health check failing)
-   Error rate > 5%
-   Database connection failures
-   LLM provider unavailable

Warning Alerts (monitored):
-   Response time p95 > 2s
-   Queue depth > 1000 jobs
-   Disk usage > 80%
-   Memory usage > 85%

## 14.5 Tracing (Future)

Distributed Tracing:
-   OpenTelemetry integration
-   Trace context propagation
-   Span correlation across services

------------------------------------------------------------------------

# 15. Data Migration & Backup

## 15.1 Database Migrations

Tool: Alembic (SQLAlchemy migrations)

Migration Workflow:
1. Create migration: `alembic revision --autogenerate -m "description"`
2. Review generated migration
3. Test migration on staging
4. Apply in production: `alembic upgrade head`

Migration Rules:
-   Never delete columns in production (deprecate first)
-   Add columns as nullable or with defaults
-   Large data migrations run as background jobs
-   Rollback plan for every migration

## 15.2 Backup Strategy

Database Backups:
-   Full backup: Daily at 02:00 UTC
-   Incremental: Every 6 hours
-   Retention: 30 days
-   Storage: Separate S3 bucket (different region)

S3 Data:
-   Versioning enabled on all buckets
-   Cross-region replication for production
-   Lifecycle rules for old versions (90 days)

Backup Verification:
-   Weekly restore test to staging
-   Automated backup integrity checks

## 15.3 Disaster Recovery

Recovery Time Objective (RTO): 4 hours
Recovery Point Objective (RPO): 6 hours

Recovery Procedures:
1. Database: Restore from latest backup
2. S3: Already replicated, switch region
3. Application: Redeploy from container registry
4. Configuration: Stored in Coolify (backed up)

## 15.4 Data Export

User Data Export:
-   GDPR-compliant data export
-   Includes: chats, documents, settings
-   Format: JSON + attachments as ZIP
-   Async processing via background worker

------------------------------------------------------------------------

# 16. Environment Variables

Environment variables are used to configure the application across different
environments. The design principle is to minimize secrets and prefer
runtime-derived or on-chain configurations where possible.

## 10.1 Security Principles

-   Minimize secrets: Prefer wallet-based authentication over API keys
-   No secrets in frontend: Frontend must never contain sensitive credentials
-   On-chain configuration: Use NFT metadata for permissions instead of env vars
-   Runtime derivation: Derive values from blockchain state when possible
-   Secret rotation: Design for easy secret rotation without redeployment

## 10.2 Backend Environment Variables

Required:

| Variable | Description | Secret |
|----------|-------------|--------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string for job queue | Yes |
| `S3_ENDPOINT` | S3-compatible storage endpoint | No |
| `S3_ACCESS_KEY` | S3 access key | Yes |
| `S3_SECRET_KEY` | S3 secret key | Yes |
| `S3_BUCKET_NAME` | Default bucket name | No |

Amini0 Auth Integration:

| Variable | Description | Secret |
|----------|-------------|--------|
| `AMINI0_BASE_URL` | Amini0 Auth Service base URL | No |
| `AMINI0_JWT_ALGORITHM` | JWT algorithm: `HS256` or `RS256` | No |
| `AMINI0_JWT_SECRET` | Shared secret for HS256 (dev only) | Yes |
| `AMINI0_JWT_PUBLIC_KEY_URL` | URL to fetch RS256 public key (prod) | No |
| `AMINI0_ADMIN_API_KEY` | API key for Amini0 Admin API (optional) | Yes |

Note: For RS256 (recommended for production), Bridge Platform fetches the public key
from Amini0's JWKS endpoint. For HS256 (development), use shared secret.

LLM Configuration:

| Variable | Description | Secret |
|----------|-------------|--------|
| `LLM_PROVIDER` | Provider name: `openai` or `amini` | No |
| `OPENAI_API_KEY` | OpenAI API key (development only) | Yes |
| `AMINI_LLM_ENDPOINT` | AminiLLM API endpoint (production) | No |
| `AMINI_LLM_API_KEY` | AminiLLM API key (production) | Yes |

Blockchain Configuration (NFT IAM Contracts):

| Variable | Description | Secret |
|----------|-------------|--------|
| `AMINICHAIN_RPC_URL` | Aminichain RPC endpoint | No |
| `AMINICHAIN_CHAIN_ID` | Chain ID for Aminichain | No |
| `NFT_IDENTITY_CONTRACT` | Identity NFT contract address (ERC-721) | No |
| `NFT_POLICY_CONTRACT` | Policy contract address | No |
| `NFT_GROUP_CONTRACT` | Group contract address | No |
| `NFT_ROLE_CONTRACT` | Role contract address | No |
| `NFT_BOUNDARY_CONTRACT` | PermissionBoundary contract address | No |
| `NFT_IAM_CACHE_TTL_SECONDS` | Permission cache TTL (default: 300) | No |

Note: All NFT IAM contract addresses are deployed and managed by Amini0.
See [NFT IAM TRD](TRD_nft_iam.md) for contract specifications.

MMDI Integration:

| Variable | Description | Secret |
|----------|-------------|--------|
| `MMDI_BASE_URL` | MMDI REST API base URL | No |
| `MMDI_WEBHOOK_SECRET` | Shared secret for webhook validation | Yes |
| `MMDI_DEFAULT_QUALITY` | Default quality level (1-4) | No |
| `MMDI_TIMEOUT_SECONDS` | Request timeout for MMDI API calls | No |
| `MMDI_POLL_INTERVAL_SECONDS` | Polling interval for job status (fallback) | No |

Default MMDI URL: `https://mmdi-rest.bbd.prd.amini.ai/api/v1`

Amini RAG Integration (Optional MCP Service):

| Variable | Description | Secret |
|----------|-------------|--------|
| `AMINI_RAG_ENABLED` | Enable Amini RAG MCP tool (default: false) | No |
| `AMINI_RAG_API_URL` | Amini RAG REST API base URL | No |
| `AMINI_RAG_MCP_URL` | Amini RAG MCP server endpoint | No |
| `AMINI_RAG_API_KEY` | API key for Amini RAG service | Yes |
| `AMINI_RAG_DEFAULT_MODE` | Default RAG query mode (default: hybrid) | No |
| `AMINI_RAG_TIMEOUT_SECONDS` | Request timeout for RAG queries | No |

Default URLs:
- REST API: `https://amini-rag.bbd.prd.amini.ai:8000`
- MCP Server: `https://amini-rag.bbd.prd.amini.ai:8001`

Note: Amini RAG is an optional MCP service. When enabled, it is registered as a
global tool that users can attach to their chats for knowledge graph queries.
This is separate from the built-in Local Search feature.

Optional:

| Variable | Description | Secret | Default |
|----------|-------------|--------|---------|
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins | No | `*` |
| `MAX_UPLOAD_SIZE_MB` | Max file upload size | No | `50` |
| `WORKER_CONCURRENCY` | Background worker threads | No | `4` |

## 10.3 Frontend Environment Variables

The frontend must NOT contain any secrets. All sensitive operations are
performed through the backend API or Amini0 Auth Service.

Build-time Variables (public, embedded in bundle):

| Variable | Description |
|----------|-------------|
| `PUBLIC_API_URL` | Bridge Platform Backend API base URL |
| `PUBLIC_AMINI0_URL` | Amini0 Auth Service base URL |
| `PUBLIC_AMINI0_OAUTH_REDIRECT_URL` | OAuth callback URL for Amini0 |
| `PUBLIC_WS_URL` | WebSocket endpoint for real-time features |
| `PUBLIC_AMINICHAIN_RPC_URL` | Aminichain RPC for wallet interactions |
| `PUBLIC_AMINICHAIN_CHAIN_ID` | Chain ID for wallet network switching |
| `PUBLIC_NFT_IDENTITY_CONTRACT` | Identity NFT contract for UI display |

Note: All frontend environment variables are prefixed with `PUBLIC_` to
indicate they are safe to expose in the browser. Only the Identity contract
address is needed on frontend - permission evaluation happens on backend.

Authentication Flow:
-   Frontend authenticates directly with Amini0 (`PUBLIC_AMINI0_URL`)
-   Amini0 returns JWT tokens
-   Frontend sends access_token to Bridge Platform API (`PUBLIC_API_URL`)
-   Token refresh is handled directly with Amini0

## 10.4 Secrets Management Strategy

Development:

-   Use `.env` files (gitignored)
-   Use `.env.example` as template (committed, no real values)

Production (Coolify):

-   Store secrets in Coolify's environment variable manager
-   Use Docker secrets where supported
-   Rotate secrets via Coolify dashboard without code changes

Secrets to Avoid:

-   User credentials (use wallet signatures instead)
-   Per-user API keys (store encrypted in database, not env vars)
-   MCP tool credentials (stored per-user in database)

## 10.5 Environment Files Structure

```
backend/
├── .env                 # Local development (gitignored)
├── .env.example         # Template with dummy values (committed)
├── .env.test            # Test environment (gitignored)

frontend/
├── .env                 # Local development (gitignored)
├── .env.example         # Template with dummy values (committed)
├── .env.production      # Production build values (gitignored)
```

------------------------------------------------------------------------

# 17. Definition of Done (DoD)

A feature is complete only if:

-   Use cases implemented
-   Unit tests written
-   BDD scenarios written
-   Coverage ≥ 70%
-   CI passing
-   Docker build successful

------------------------------------------------------------------------

# 18. MVP Scope

Included:

-   Chat with streaming (AminiLLM / ChatGPT)
-   LLM-powered document authoring assistance
-   MCP tool attachment per chat
-   User-owned MCP tool libraries
-   Markdown documents
-   Folder tree
-   Comments with resolution
-   Document sharing and collaborative review
-   File uploads via MMDI (PDF, DOCX, XLSX, CSV, images)
-   Local Search via pgvector (embeddings from MMDI-extracted content)
-   Optional Amini RAG MCP integration (external knowledge graph queries)
-   Admin tool control
-   Amini0 authentication (email/password, OAuth, wallet SIWE)
-   NFT IAM smart contracts for AWS IAM-style permissions
-   Three-layer permission model (identity, group, role policies)
-   Minimal secrets architecture
-   BDD + TDD enforcement

Deferred:

-   Real-time collaborative editing
-   Advanced graph analytics
-   Enterprise multi-tenancy
-   Video file processing (MMDI placeholder)

------------------------------------------------------------------------

# 19. Conclusion

The AI Bridge Platform combines:

-   LLM-powered conversational AI (AminiLLM production / ChatGPT development)
-   Attachable MCP tools (global and user-owned)
-   Obsidian-style document management
-   Structured Markdown authoring with comments
-   Document sharing and collaborative review with permission levels
-   Folder-based organization
-   Multi-format file ingestion via MMDI (PDF, DOCX, XLSX, CSV, images)
-   Dual search system: Local Search (pgvector) + optional Amini RAG (MCP)
-   Centralized authentication via Amini0 Auth Service
-   AWS IAM-style permissions via NFT IAM smart contracts (on Aminichain)
-   Three-layer permission model (identity → group → role policies)
-   Hexagonal backend architecture
-   MVVM frontend architecture with MCP-driven functionality model
-   Thin-client frontend with minimal UI changes for new features
-   Production-ready containerized deployment
-   Strict quality enforcement (BDD + TDD + ≥70% coverage)

Related Documentation:
-   [Amini0 TRD](🔐%20Amini0%20TRD.md) - Authentication service specification
-   [NFT IAM TRD](TRD_nft_iam.md) - NFT-based identity and access management contracts
-   [MMDI TRD](TRD_MMDI.md) - Multimodal Data Ingestion service specification
-   [Amini RAG TRD](TRD_AMINI_RAG.md) - Knowledge Graph RAG service specification (optional MCP)
