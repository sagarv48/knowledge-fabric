# Phase 1: Knowledge Fabric

## Purpose

Knowledge Fabric is a vendor-neutral, MCP-native evidence retrieval platform.

It answers this problem:

```text
How do we give AI the right context before it answers?
```

It does not execute workflows, create cases, call runtime platform APIs, or require runtime platform credentials.

## Core flow

```text
User query
  -> Knowledge Fabric MCP
  -> Lexical retrieval
  -> Vector retrieval
  -> Hybrid fusion
  -> Evidence package
  -> AI assistant generates answer from evidence
```

## Scope

In scope:

- Document ingestion
- Document parsing
- Chunking
- Metadata extraction
- Embedding provider abstraction
- Lexical retrieval
- Vector retrieval
- Hybrid retrieval using RRF
- Evidence packaging
- MCP retrieval server
- Retrieval evaluation

Out of scope:

- Workflow execution
- Approval workflows
- Product-specific MCP integrations
- Case creation
- Assignment completion
- Production enterprise connectors

## Suggested repo structure

```text
knowledge-fabric/
  README.md
  docs/
  config/
  docker-compose.yml
  src/
    knowledge_fabric/
      ingestion/
      chunking/
      embeddings/
      retrieval/
      fusion/
      evidence/
      mcp/
      evaluation/
  tests/
  examples/
  sources/
```

## Manual setup steps

```bash
mkdir knowledge-fabric
cd knowledge-fabric
git init
mkdir -p docs config examples sources tests src/knowledge_fabric
mkdir -p src/knowledge_fabric/{ingestion,chunking,embeddings,retrieval,fusion,evidence,mcp,evaluation}
```

Create a local branch:

```bash
git checkout -b phase-1-knowledge-fabric
```

## Local infrastructure

Use the simplest MVP stack first:

```text
PostgreSQL + pgvector
Apache Tika
Python MCP server
```

Optional later:

```text
OpenSearch
Neo4j
Reranker service
```

## MVP exit criteria

Knowledge Fabric MVP is complete when:

- Documents are ingested.
- Chunks are created.
- Embeddings are generated or mocked behind an interface.
- Lexical retrieval works.
- Vector retrieval works.
- Hybrid RRF retrieval works.
- MCP tool `retrieve_evidence` returns evidence packages.
- Retrieval evaluation runs.
- Negative tests abstain correctly.

## Current implementation status

Implemented:

- Ingestion for markdown, txt, html, pdf, docx, pptx
- Apache Tika-based binary extraction
- Heading-aware chunking with fallback windowing
- Mock embedding provider interface
- PostgreSQL lexical retrieval and pgvector retrieval
- Hybrid retrieval with reciprocal rank fusion
- Evidence package contract
- MCP tool surface:
  - `retrieve_evidence`
  - `get_document`
  - `explain_retrieval`
- Retrieval audit logging
- Evaluation runner and sample query set

## Adoption quickstart

```bash
docker compose up -d
PYTHONPATH=src python3 -m pytest tests
```

Core package layout:

```text
src/knowledge_fabric/ingestion
src/knowledge_fabric/chunking
src/knowledge_fabric/embeddings
src/knowledge_fabric/retrieval
src/knowledge_fabric/fusion
src/knowledge_fabric/evidence
src/knowledge_fabric/mcp
src/knowledge_fabric/evaluation
```

Additional guides:

- `docs/phase-1-knowledge-fabric/local-setup.md`
- `docs/phase-1-knowledge-fabric/mcp-usage.md`
- `docs/phase-1-knowledge-fabric/retrieval-evaluation.md`
- `docs/phase-1-knowledge-fabric/real-adoption-guide.md`
- `docs/deployment-runbook.md`
