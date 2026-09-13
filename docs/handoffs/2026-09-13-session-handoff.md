# Session Hand-off: 2026-09-13

### Status: Green ✅
**Tests Across Ecosystem:**
- `knowledge-fabric`: **119 passed**, 0 failed
- `intent-fabric`: **41 passed**, 0 failed
- `knowledge-fabric-enterprise-adapters`: **73 passed**, 0 failed
- **Combined Total:** **233 passed**, 0 failed

---

## What Changed

### Deliverable 1 — Reranker Wired into MCP Server (Phase 0)
- `src/knowledge_fabric/config.py` — Added `RerankingSettings(provider, top_n)` dataclass + `reranking` field on `Settings`. Added `backend` field to `RetrievalSettings`.
- `src/knowledge_fabric/mcp/server.py` — `build_tools_from_settings()` now calls `build_reranker(settings.reranking.provider)` and passes the result to `RetrievalPipeline`. Added a warning log when `backend=qdrant` is configured but not yet supported.
- `config/settings.yaml` — Added explicit `provider: none` to the `reranking` section (was implied but absent).

### Deliverable 2 — Uniform Tenant Scoping on `get_document` and `list_sources` (Phase 0 & 1)
- `src/knowledge_fabric/retrieval/postgres.py` — `get_document()` now accepts `tenant_id` and applies `_filter_clause()` + `SET LOCAL` RLS. New `list_sources_for_tenant(tenant_id)` method replaces the un-scoped `list_sources` raw SQL.
- `src/knowledge_fabric/mcp/tools.py` — `list_sources(tenant_id)` and `get_document(tenant_id)` accept and forward tenant context.
- `src/knowledge_fabric/mcp/server.py` — Applied `validate_tenant_id()` at tool entry for `list_sources`, `get_document`, and `retrieve_evidence` to block path traversal and malformed tenant strings before DB dispatch. Supported dual FastMCP / MCPServer imports.

### Deliverable 3 — Config Model Mismatch Fixed (Phase 0)
Covered by D1 above (`backend` field, `RerankingSettings` model, explicit YAML parsing replacing `**dict` unpacking).

### Deliverable 4 — Integration Tests (Vertical Slice) (Phase 0)
- `tests/test_integration_vertical_slice.py` — 4 tests proving the full end-to-end path without a live DB. Includes the critical negative test: `get_document` with wrong tenant returns `None`.
- `tests/test_mcp_server.py` — Added `test_mcp_server_validates_tenant_boundary`.

### Deliverable 5 — README Truthfulness (Phase 0)
- CI badge changed to live GitHub Actions badge URL.
- Benchmark numbers wrapped in `> [!NOTE]` caveat: *illustrative only*.
- MCP tools table updated to match actual implementation.

### Deliverable 6 — Intent Fabric FastMCP Server Transport (Phase 1)
- `intent-fabric/pyproject.toml` — Added `"mcp>=1.10.0"` and `[project.scripts]` entry `intent-fabric-mcp = "intent_fabric.mcp.server:run_mcp_server"`.
- `intent-fabric/src/intent_fabric/mcp/server.py` — Built FastMCP server exposing `health_check`, `create_plan_from_evidence`, `validate_plan`, `create_approval_package`, `simulate_plan`, and `sign_approval`.
- `intent-fabric/src/intent_fabric/mcp/tools.py` — Added `sign_approval()` and `health_check()` methods.
- `intent-fabric/tests/test_mcp_server.py` — Comprehensive unit and tool execution tests.
- `intent-fabric/README.md` — Fixed usage snippet and added FastMCP server configuration instructions.

### Deliverable 7 — Enterprise Adapters Cryptographic Approval Gate & Path Fixes (Phase 1)
- `enterprise-adapters/src/enterprise_adapters/approvals.py` — Added `canonical_approval_payload`, `compute_approval_signature`, and `verify_approval_signature`.
- `enterprise-adapters/src/enterprise_adapters/execution.py` — Updated `ApprovedRuntimeActionAdapter.execute_action` to verify HMAC signatures on mutative actions (`write=True`) or whenever an approval token is supplied.
- `enterprise-adapters/src/enterprise_adapters/github_issue_adapter.py` — Enforced policy ALLOW, `approval_id`, and cryptographic signature verification before making external HTTP mutation requests.
- `enterprise-adapters/src/enterprise_adapters/file_source_adapters.py`, `source_adapters.py`, `standard_source_adapters.py` — Standardized on `.as_posix()` and clean newline handling, fixing the 5 Windows test failures.
- `enterprise-adapters/tests/test_crypto_approval_gate.py` — Comprehensive tests for valid, missing, permissive, and tampered approval signatures.

### Deliverable 8 — Cross-Repository Integration Test (Phase 1)
- `intent-fabric/tests/test_cross_repo_governance_slice.py` — Verifies full lifecycle from Knowledge Fabric evidence package -> Intent Fabric plan & policy -> HMAC signed approval token -> Enterprise Adapter execution and audit logging.

### Deliverable 9 — Retrieval-Leg Transparency & Multi-Mode Retrieval (Phase 5 & Cross-Phase §7)
- `src/knowledge_fabric/retrieval/pipeline.py` — Added `mode: Literal["hybrid", "lexical", "vector"] = "hybrid"` and `fail_closed: bool = False`.
  - In `lexical` mode, embedding calls are bypassed entirely.
  - In `vector` mode, text search queries are bypassed entirely.
  - In `hybrid` mode, both legs are tracked independently (`legs.lexical`, `legs.vector`) with latencies, hit counts, and status (`ok`, `error`, `skipped`).
  - Graceful degradation: If a leg fails when `fail_closed=False`, marks `strategy="degraded_lexical"` or `"degraded_vector"` and sets `is_degraded=True` with error warnings (never falsely claiming healthy hybrid).
- `src/knowledge_fabric/evidence/models.py` — `build_evidence_package` updated to accept `summary_extra` and populate per-leg metadata into `retrieval_summary`.
- `src/knowledge_fabric/mcp/tools.py` & `src/knowledge_fabric/mcp/server.py` — Expose `mode` on `retrieve_evidence` and `tenant_id` + `mode` on `explain_retrieval`.
- `tests/test_retrieval_pipeline.py` & `tests/test_mcp_server.py` — Comprehensive unit tests covering single-leg bypass, degraded hybrid, fail-closed handling, and invalid mode rejection.

### Deliverable 10 — Safe Deletion, Tenant Purge & Data Model Invariants (Phase 1, 2 & 9)
- `docs/data-model.md` — Authored canonical data model specification detailing entity definitions (`documents`, `chunks`, `retrieval_runs`, `audit_events`), composite indexes, foreign key cascading cleanup (`ON DELETE CASCADE`), dual-mode multi-tenancy isolation (Mode 1 application filter + Mode 2 PostgreSQL RLS), and data integrity verification queries.
- `src/knowledge_fabric/db/repository.py` — Added `delete_document(document_id, source_uri, tenant_id)`, `delete_by_source(source_type, tenant_id)`, and `purge_tenant(tenant_id)`.
  - Scoped to `tenant_id` to prevent cross-tenant deletions.
  - Deleting a document automatically cascades to all child chunks and embeddings.
  - `purge_tenant` atomically clears all documents, chunks, retrieval runs, and audit events for that tenant.
- `src/knowledge_fabric/retrieval/store.py` & `postgres.py` — Added `get_document`, `delete_document`, and `purge_tenant` to `RetrievalStore` protocol and `PostgresRetrievalStore`.
- `src/knowledge_fabric/ingestion/cli.py` — Added CLI arguments for `--delete-document-id`, `--delete-source-uri`, `--delete-source-type`, and `--purge-tenant` (with `--confirm`).
- `tests/test_db_repository.py` & `tests/test_ingestion_cli.py` — Added unit and CLI tests covering document deletion, source deletion, full tenant purge, confirmation guards, and path traversal rejection.

### Deliverable 11 — Retrieval Evaluation, Categorized Datasets & Quality Gates (Phase 8)
- `src/knowledge_fabric/evaluation/queries.yaml` — Upgraded with versioned schema (`v1.0.0`), `dataset_id`, license, provenance, embedded seed corpus, and 12 categorized evaluation queries (`exact`, `paraphrase`, `disagreement`, `metadata`, `unanswerable`).
- `src/knowledge_fabric/evaluation/runner.py` — Built end-to-end evaluation runner:
  - Supported metrics: **Recall@10**, **Precision@5**, **MRR**, **NDCG@10** (binary & graded), **No-Result Accuracy** (for unanswerable queries), and latency percentiles (avg, p95).
  - Category breakdown: per-category metrics across all modes.
  - `EvaluationReport` container with dictionary-compatible access, JSON serialization (`to_json()`), and GitHub-formatted Markdown tables (`to_markdown()`).
  - Quality gates: `check_quality_gates(min_mrr, min_recall, min_ndcg)`.
  - Self-contained `InMemoryEvaluationStore` and `create_seed_pipeline` for offline CI evaluation without database requirements.
  - `make_pipeline_retriever` adapter linking `RetrievalPipeline` to evaluation.
  - CLI entry point `main()` registered as `knowledge-fabric-eval` in `pyproject.toml`.
- `docs/retrieval-evaluation.md` & `docs/evaluation/baseline_report.md` — Detailed methodology, dataset specifications, metrics definitions, and baseline evaluation reports.
- `tests/test_evaluation_runner.py` — 10 unit and integration tests verifying metric calculations, category aggregations, unanswerable queries, report outputs, quality gates, and CLI execution.

### Deliverable 12 — Observability, Diagnostics, Direct Evidence & Consistency (Phase 7 & 10)
- `src/knowledge_fabric/db/repository.py` & `retrieval/postgres.py`:
  - `get_chunk`: Fetches single chunk by chunk ID with document URI, source type, title, and metadata scoped to tenant.
  - `get_index_status`: Queries total documents, total chunks, and source distribution breakdown (document count, chunk count, last updated timestamp).
  - `check_consistency`: Audits relational database invariants (orphaned chunks, empty documents, null tenants, unpopulated embeddings).
  - `reembed_chunks`: In-place batch re-embedding of chunks using configured embedding provider without re-parsing files.
- `src/knowledge_fabric/mcp/tools.py` & `src/knowledge_fabric/mcp/server.py`:
  - Exposed MCP tools: `get_index_status`, `get_evidence`, and `check_consistency`.
- `src/knowledge_fabric/ingestion/cli.py`:
  - Added CLI flags: `--index-status`, `--check-consistency`, and `--reembed`.
- `docs/operations-runbook.md`:
  - Authored operations runbook covering system health, index status inspection, consistency validation, model re-embedding, tenant offboarding, and PostgreSQL pgvector backup/restore.
- `tests/test_operations_and_observability.py`:
  - 7 unit tests verifying `get_chunk`, `get_index_status`, `check_consistency` (healthy and unhealthy), `reembed_chunks`, and MCP tool registrations.
- `tests/test_ingestion_cli.py`:
  - Added CLI tests covering `--index-status`, `--check-consistency`, and `--reembed`.

### Deliverable 13 — Synthetic Scale Benchmark & Capability Truth Validation (Phase 11)
- `benchmarks/synthetic_scale.py`:
  - Configurable synthetic corpus and vector benchmark generator.
  - Measures ingestion throughput (chunks/sec), cold vs warm query latency percentiles (p50, p95, p99), and per-mode performance (lexical, vector, hybrid RRF).
  - Captures exact hardware specs (CPU, OS, Python version) to enforce capability truth and prevent exaggerated production claims.

### Deliverable 14 — Multi-Format Ingestion & Structure-Aware Chunking (Phase 2 & 3)
- `src/knowledge_fabric/ingestion/models.py`:
  - Enriched `Document` with `content_hash` (deterministic SHA-256), `content_length`, `headings`, and `page_count`.
  - Enriched `Chunk` with `heading_path` (breadcrumb string), `heading_level` (int), `content_hash` (deterministic SHA-256), `start_offset`, and `end_offset`.
  - Automatic `metadata` synchronization in `__post_init__` ensures all downstream citation generators, APIs, and database stores receive structural attributes without schema disruption.
  - Added `IngestionRecord` and `IngestionStatus` (`added`, `updated`, `unchanged`, `failed`) for lifecycle tracking.
- `src/knowledge_fabric/ingestion/service.py`:
  - Added `max_file_size_bytes` guard (default 25MB) with immediate validation to prevent unbounded memory spikes.
  - Extracted markdown headings and HTML headings/titles into canonical document metadata while preserving file stem titles.
- `src/knowledge_fabric/chunking/service.py`:
  - Implemented `ChunkingConfig` with `preserve_code_blocks` and `preserve_tables`.
  - Built `MarkdownStructureChunker` that maintains a hierarchical heading stack (`heading_path`: `# A > ## B > ### C`), decomposes oversized sections into atomic structural blocks, and avoids splitting fenced code blocks (```` ``` ````) or markdown tables (`|...|`).
  - Implemented `PageAwareChunker` detecting form-feed (`\f`) and slide markers (`--- Page X ---`), attributing each chunk with its exact `page_number`.
  - Preserved fallback sliding character window for plain text.
- `src/knowledge_fabric/ingestion/cli.py`:
  - Added `--max-file-size-mb` CLI parameter (default: 25).
  - Implemented document-level failure isolation in the ingestion loop, allowing successful files to proceed while capturing errors cleanly in the run summary.
- Tests Added:
  - `tests/test_chunking.py`: Added 5 new tests verifying heading breadcrumb paths, code block atomicity, table atomicity, exact slice offsets, SHA-256 content hashes, and page-aware chunking.
  - `tests/test_ingestion.py`: Added 5 new tests verifying content hashes, max file size enforcement, markdown/HTML heading extraction, and `IngestionRecord` data models.
  - `tests/test_ingestion_cli.py`: Added test verifying `--max-file-size-mb` execution and document-level failure isolation.

---

## Ecosystem Test Suite Status (233 Tests Passing)

- `knowledge-fabric`: **119 passed**, 0 failed
- `intent-fabric`: **41 passed**, 0 failed
- `knowledge-fabric-enterprise-adapters`: **73 passed**, 0 failed
**Total: 233 passed across all 3 repositories.**

---

## Known Limitations / Next Recommended Tasks

| Item | Status | Notes |
|---|---|---|
| Multi-Format Ingestion & Structure-Aware Chunking (Roadmap Phase 2 & 3) | 🟢 Completed | Hierarchical heading paths, code/table atomicity, offsets, content hashes, page awareness, 25MB guard |
| Ground-Truth Evaluation Dataset & Quality Gates (Roadmap Phase 8) | 🟢 Completed | Versioned dataset, metrics (Recall@10, Precision@5, MRR, NDCG@10, No-Result Acc), CLI `knowledge-fabric-eval` & report generator |
| Observability, Diagnostics & Operations Runbook (Roadmap Phase 10) | 🟢 Completed | `get_index_status`, `get_evidence`, `check_consistency`, `reembed_chunks`, `docs/operations-runbook.md` |
| Scale & Benchmark Synthetic Generator (Roadmap Phase 11) | 🟢 Completed | `benchmarks/synthetic_scale.py` measuring throughput, cold/warm p50/p95/p99 latency, and hardware manifest |
| Docker Compose Prod Audit | 🟡 Recommended | Verify prod compose services run cleanly with migrations |
| Live Embedding Benchmark (Ollama / OpenAI) | ⚪ Optional | Run `knowledge-fabric-eval` against a live embedding model for calibrated semantic benchmarks |
| Qdrant ingestion path | ⚪ Deferred | Ingestion pipeline writes to Postgres/pgvector; Qdrant is experimental |


