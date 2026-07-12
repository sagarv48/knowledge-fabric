# Knowledge Fabric Architecture

Knowledge Fabric is a vendor-neutral evidence retrieval platform designed to provide grounded context for AI assistants.

## System intent

- Ingest and normalize source documents
- Build retrieval-ready chunks and metadata
- Support lexical, vector, and hybrid retrieval
- Return evidence packages through MCP tools

## High-level flow

```text
User Query
    ->
Retrieval Pipeline
    ->
Evidence Package
    ->
AI Assistant
```

## Retrieval pipeline

```text
Sources
  ->
Ingestion (md/txt/html/pdf/docx/pptx)
  ->
Chunking (heading-aware + fallback windowing)
  ->
Indexing (full-text + vector)
  ->
Retrieval (lexical + vector)
  ->
Hybrid Fusion (RRF)
  ->
Evidence Package
```

## Runtime components

```text
PostgreSQL + pgvector
  - documents
  - chunks
  - retrieval_runs
  - audit_events

Apache Tika
  - binary text extraction for pdf/docx/pptx

Knowledge Fabric MCP Server
  - retrieve_evidence
  - get_document
  - explain_retrieval
```

## Data model summary

- **Document**: canonical source record with text and metadata.
- **Chunk**: retrieval unit with chunk text, positional context, and metadata.
- **RetrievalHit**: scored hit returned by lexical/vector retrieval.
- **HybridHit**: fused hit from reciprocal rank fusion.
- **EvidencePackage**: structured response payload for downstream assistants.

## Non-goals

- Workflow execution
- Approval orchestration
- Product-specific runtime connectors
