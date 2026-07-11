# Knowledge Fabric

Knowledge Fabric is an MCP-native evidence retrieval platform for open-source use. It ingests source material, builds lexical and vector indexes, performs hybrid retrieval, and returns structured evidence packages for AI assistants.

## Project Overview

Knowledge Fabric provides vendor-neutral retrieval primitives that improve answer quality by grounding responses in retrieved evidence.

## Architecture

```text
User Query
    ↓
Knowledge Fabric
    ↓
Evidence Package
    ↓
AI Assistant
```

Core retrieval pipeline:

```text
ingestion -> chunking -> embeddings -> lexical retrieval + vector retrieval -> hybrid fusion -> evidence packaging -> MCP retrieval tools
```

## Features

- Document ingestion and parsing
- Chunking and metadata extraction
- Embedding provider abstraction
- Lexical retrieval
- Vector retrieval
- Hybrid retrieval with rank fusion
- Evidence package contract
- MCP-native retrieval endpoints
- Retrieval evaluation framework

## Roadmap

1. Stabilize ingestion and chunking interfaces.
2. Expand retrieval evaluation benchmarks and datasets.
3. Add optional pluggable reranking components.
4. Improve deployment examples for local and containerized development.

## Getting Started

```bash
git clone <repository-url>
cd knowledge-fabric
```

Read the project guides in `docs/`:

- `docs/README.md`
- `docs/repo-boundaries.md`
- `docs/phase-1-knowledge-fabric/README.md`

## Contributing

See `CONTRIBUTING.md` for contribution workflow, coding expectations, and review process.

## License

This project is licensed under the Apache License 2.0. See `LICENSE`.

## Non-goals

- Runtime workflow execution
- Product-specific integrations
- Customer-specific adapters and deployment details
- Credential management for external enterprise systems
