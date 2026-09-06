# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-09-06

### Added
- Visual Admin & Governance Console (`knowledge-fabric-ui`) with zero frontend build dependencies, serving an interactive approval queue, live retrieval playground, and policy test sandbox.
- Production Helm chart (`deploy/helm/knowledge-fabric`) with flexible embedded pgvector or external DB options, HPA, Ingress TLS, and Kubernetes secret management.
- Multi-stage production `Dockerfile` with non-root user (`UID 10001`), healthchecks, and `docker-compose.prod.yml` turnkey deployment.
- High-scale vector search optimizations with HNSW indexing migration (`005_hnsw_indexes.sql`), PostgreSQL declarative tenant partitioning, and zero-dependency `QdrantRetrievalStore` adapter.
- STRIDE security hardening: strict tenant ID validation (`^[a-zA-Z0-9_.:@-]{1,128}$`), query length bounds, top_k bounds [1, 100], reranker candidate pool capping, and HMAC approval signature validation.
- Backwards-compatible CLI argument aliases (`--source-path`, `--collection`, `--source-type`) in `knowledge_fabric.ingestion.cli`.

### Changed
- Standardized ruff and pyright CI workflows with Python 3.11 and 3.12 support.
- Configured production database user default to `knowledge_fabric`.

## [0.1.0] - 2026-07-12

### Added
- Core Knowledge Fabric retrieval pipeline with hybrid RRF fusion (lexical FTS + vector similarity via pgvector).
- Pluggable embedding providers (Ollama, OpenAI, Cohere, Mock).
- Document ingestion pipeline supporting Markdown, text, and JSON with chunking and metadata extraction.
- FastMCP tool server integration (`retrieve_evidence`, `get_document`, `explain_retrieval`, `health_check`, `list_sources`).
