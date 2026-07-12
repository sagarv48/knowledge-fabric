# Knowledge Fabric Phase 1 Real Adoption Guide

This guide walks through a practical, end-to-end Phase 1 setup so developers can run and evaluate Knowledge Fabric locally.

## 1. Prerequisites

- Python 3.11+
- Docker and Docker Compose
- A PostgreSQL client (optional but recommended)

## 2. Clone and install

```bash
git clone <repository-url>
cd knowledge-fabric
python3 -m pip install -e ".[dev]"
```

## 3. Start local infrastructure

```bash
docker compose up -d
```

This starts:

- PostgreSQL + pgvector on `localhost:5432`
- Apache Tika on `localhost:9998`

Schema files under `db/schema/` are applied automatically on first startup.

## 4. Run baseline tests

```bash
python3 -m pytest
```

## 5. Ingest source documents

Use `DocumentIngestionService` for Markdown, TXT, HTML, PDF, DOCX, and PPTX:

```python
from knowledge_fabric.ingestion import DocumentIngestionService, TikaClient
from knowledge_fabric.chunking import DocumentChunkingService

tika = TikaClient(endpoint="http://localhost:9998")
ingestion = DocumentIngestionService(tika_client=tika)
chunking = DocumentChunkingService(max_chars=1200, overlap_chars=150)

document = ingestion.ingest_file("sources/example.md", source_metadata={"collection": "default"})
chunks = chunking.chunk_document(document)
print(document.source_uri, len(chunks))
```

## 6. Persist documents/chunks

Use the persistent ingestion CLI:

```bash
knowledge-fabric-ingest --path sources --recursive --embed
```

This command ingests supported files, chunks content, optionally creates mock embeddings, and writes data to:

- `documents`
- `chunks`

## 7. Wire retrieval components

Use:

- `PostgresRetrievalStore` for lexical/vector retrieval
- `MockEmbeddingProvider` for query embeddings
- `RetrievalPipeline` for hybrid fusion + evidence packaging
- `AuditLogger` for retrieval telemetry
- `KnowledgeFabricMCPTools` for tool-style access

Reference bootstrap:

`examples/mcp_tool_bootstrap.py`

## 8. Run retrieval end-to-end

```python
tools = build_tools(connection_factory)  # from examples/mcp_tool_bootstrap.py

evidence = tools.retrieve_evidence("vector retrieval with pgvector", top_k=5)
doc = tools.get_document(source_uri="sources/example.md")
trace = tools.explain_retrieval("vector retrieval with pgvector", top_k=5)

print(evidence["retrieval_summary"])
print(doc["title"] if doc else "document not found")
print(trace["trace"])
```

## 9. Evaluate quality

Evaluation query set:

`src/knowledge_fabric/evaluation/queries.yaml`

Runner:

`knowledge_fabric.evaluation.RetrievalEvaluationRunner`

Metrics:

- Recall@10
- Precision@5
- MRR
- NDCG@10

## 10. Recommended adoption path

1. Start with Markdown/TXT ingestion.
2. Add binary formats (PDF/DOCX/PPTX) through Tika.
3. Persist and validate lexical retrieval first.
4. Enable vector retrieval and compare lexical/vector/hybrid metrics.
5. Expose MCP tools to your assistant runtime.

## 11. Non-goals in this repository

- Workflow execution
- Approval workflows
- Runtime product-specific connectors

## 12. Troubleshooting

- **No retrieval hits**: verify `documents`/`chunks` tables contain records.
- **Binary extraction empty**: verify Tika is reachable at `http://localhost:9998/tika`.
- **Vector search errors**: verify `vector` extension is installed and embeddings are stored in `chunks.embedding`.
- **CLI command not found**: run `python3 -m pip install -e ".[dev]"` to install project scripts.
