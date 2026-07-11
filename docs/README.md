# Phase 1: Knowledge Fabric

## Purpose

Knowledge Fabric is a vendor-neutral, MCP-native evidence retrieval platform. We assume Acme is an organization which want to use knowledge fabric and intent fabric with its platform/mcp and knowledgebases.

It answers this problem:

```text
How do we give AI the right context before it answers?
```

It does not execute workflows, create cases, call Acme APIs, or require Acme credentials.

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
- Acme MCP
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
