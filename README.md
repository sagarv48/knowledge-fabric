# Knowledge Fabric

Knowledge Fabric is a vendor-neutral evidence retrieval platform.

In plain terms: it helps an assistant find the right context before generating a response. Instead of jumping straight to “an answer,” it returns a structured **evidence package** that downstream assistants can use for grounded output.

## Why this project exists

Many assistant failures come from missing or weak context, not from poor generation quality.  
Knowledge Fabric focuses on that retrieval layer so teams can improve relevance, traceability, and trust.

## What it does (Phase 1)

- Ingests source content (markdown, text, html, pdf, docx, pptx)
- Chunks and normalizes content for retrieval
- Supports lexical search, vector search, and hybrid fusion
- Returns evidence packages through MCP tools
- Tracks retrieval telemetry and evaluation metrics

## Architecture

```text
User Query
    ->
Knowledge Fabric
    ->
Evidence Package
    ->
AI Assistant
```

Retrieval pipeline:

```text
Sources
  ->
Ingestion
  ->
Chunking
  ->
Embeddings
  ->
Lexical + Vector Retrieval
  ->
Hybrid Fusion (RRF)
  ->
Evidence Package
```

## Quick start

```bash
git clone <repository-url>
cd knowledge-fabric
python3 -m pip install -e ".[dev]"
docker compose up -d
python3 -m pytest
```

Run persistent ingestion:

```bash
knowledge-fabric-ingest --path sources --recursive --embed
```

Run MCP server:

```bash
knowledge-fabric-mcp
```

## MCP tools

- `retrieve_evidence`
- `get_document`
- `explain_retrieval`

These tools return retrieval outputs and metadata, not final prose answers.

## Documentation map

- `docs/README.md`
- `docs/architecture.md`
- `docs/local-setup.md`
- `docs/evidence-package-contract.md`
- `docs/retrieval-evaluation.md`
- `docs/model-provider-strategy.md`
- `docs/security-and-data-boundaries.md`
- `docs/deployment-runbook.md`
- `docs/phase-1-knowledge-fabric/README.md`

## Current roadmap

1. Expand evaluation datasets and benchmarks.
2. Add optional reranking extension points.
3. Improve ingestion operational ergonomics for larger corpora.
4. Continue hardening local-to-production deployment guidance.

## Contributing

Contributions are welcome. If you’re fixing a bug or adding retrieval capabilities, please include tests and docs updates in the same change whenever possible.

See `CONTRIBUTING.md` for full workflow details.

## License

Apache License 2.0. See `LICENSE`.

## Non-goals

- Workflow execution
- Approval orchestration
- Product-specific integrations
- Customer-specific deployment internals
