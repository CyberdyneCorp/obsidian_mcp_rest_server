# Future Roadmap

## Goal
Evolve the Obsidian Vault MCP/REST Server from a production-ready core into a scalable, secure, collaborative platform.

## Planning Assumptions
- Current baseline is stable: tests/lint/types pass.
- Core single-tenant-per-user workflows are implemented.
- Roadmap prioritizes risk reduction first, then product expansion.

## Phase 1: GA Hardening (0-2 months)
### Objectives
- Raise operational safety and security posture before broader adoption.

### Deliverables
- Access control:
  - Add role-based access control (owner/editor/viewer) at vault level.
  - Add team/workspace model (initial version).
- Security:
  - Token revocation strategy (logout-all, compromised token handling).
  - Optional MFA + SSO/OIDC integration design and first implementation.
  - Tighten CORS policy by environment (no wildcard in production).
- Operations:
  - Add metrics, tracing, and health depth checks (DB/vector/graph dependencies).
  - Define SLOs and alerts (availability, p95 latency, ingestion failures).
  - Add backup/restore runbook and automated backup verification.
- API stability:
  - API versioning policy (`/v1`) and compatibility guidelines.
  - Idempotency support for write-heavy endpoints (ingest/import).

### Exit Criteria
- On-call alerting active with tested runbooks.
- Security review completed with no critical findings.
- Vault sharing and role enforcement validated by integration tests.

## Phase 2: Sync and Scale (2-4 months)
### Objectives
- Improve throughput, reliability, and data freshness for larger vaults.

### Deliverables
- Background processing:
  - Queue-based jobs for ingestion, embeddings, graph rebuilds.
  - Retry, dead-letter queue, and job observability dashboards.
- Incremental sync:
  - Change detection and partial re-indexing (avoid full re-ingest).
  - Conflict handling strategy for concurrent updates.
- Performance:
  - Query/index tuning for large vaults and table-heavy workloads.
  - Rate-limit policies tuned by endpoint and tenant.
- Multi-tenant guardrails:
  - Tenant-aware quotas (storage, requests, embeddings).
  - Usage accounting for future billing hooks.

### Exit Criteria
- Large-vault benchmarks meet defined SLOs.
- Re-index latency and job failure rates tracked and within thresholds.
- Incremental sync covers common edit/delete/rename scenarios.

## Phase 3: Search and Knowledge Quality (4-6 months)
### Objectives
- Improve relevance, discoverability, and graph usefulness.

### Deliverables
- Retrieval quality:
  - Hybrid retrieval tuning (semantic + full-text weighting).
  - Result re-ranking with metadata and link signals.
  - Query suggestions, typo tolerance, and synonym support.
- Knowledge graph quality:
  - Better entity/link normalization and alias resolution.
  - Link quality diagnostics (orphan, dead-link, hub anomaly insights).
- Attachment intelligence:
  - OCR and PDF text extraction pipeline.
  - Search across extracted attachment text.

### Exit Criteria
- Measurable search quality gains on benchmark queries.
- Attachment text appears in searchable corpus with acceptable latency.

## Phase 4: Collaboration and Product Surface (6-9 months)
### Objectives
- Expand from backend service to full collaborative platform capabilities.

### Deliverables
- Collaboration:
  - Shared vault workflows, invitations, and access lifecycle.
  - Audit trail for sensitive actions.
- Data governance:
  - Soft-delete with restore window.
  - Retention policies and compliance-ready exports.
- Developer ecosystem:
  - Stable SDK generation for REST + MCP clients.
  - Public API docs with versioned changelogs and migration notes.

### Exit Criteria
- Team sharing workflows validated end-to-end.
- Governance controls configurable per workspace.
- SDK consumers can complete core flows without custom wrappers.

## Cross-Cutting Tracks (All Phases)
- Testing:
  - Keep BDD scenarios aligned to roadmap features.
  - Add contract tests for API/MCP compatibility.
- Documentation:
  - Update TRD and operational runbooks at each phase gate.
  - Publish breaking-change policy and migration guides.
- Architecture:
  - Preserve Hexagonal boundaries as features grow.
  - Track architectural decisions with ADRs.

## Prioritization Backlog
### P0 (Must-Have Before Broad External Rollout)
- RBAC + workspace model
- Security hardening (token revocation, env-specific CORS)
- Observability + SLO alerting
- Backup/restore automation

### P1 (High-Value Next)
- Async job processing and incremental sync
- Hybrid search quality improvements
- Usage quotas and tenant guardrails

### P2 (Strategic Expansion)
- OCR/PDF enrichment
- Collaboration UX/API completeness
- SDK ecosystem and public developer experience

## Suggested Cadence
- 2-week iterations.
- Monthly roadmap checkpoint:
  - Re-rank backlog using incident data, latency/error trends, and customer feedback.
- Phase gate review at end of each phase with explicit go/no-go criteria.

