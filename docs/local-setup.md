# Knowledge Fabric Local Setup

This guide sets up a local, vendor-neutral Phase 1 environment for evidence retrieval.

## Prerequisites

- Python 3.11+
- Docker + Docker Compose

## 1. Clone and install dependencies

```bash
git clone <repository-url>
cd knowledge-fabric
python3 -m pip install -e ".[dev]"
```

## 2. Start infrastructure

```bash
docker compose up -d
```

Services started:

- **PostgreSQL + pgvector** on `localhost:5432`
- **Apache Tika** on `localhost:9998`

Database schema initialization runs from:

`db/schema/`

## 3. Verify tests

```bash
python3 -m pytest
```

## 4. Run MCP server

```bash
python3 -m knowledge_fabric.mcp
```

## 5. Optional local workflow

```text
Ingest files -> Chunk documents -> Store in PostgreSQL -> Retrieve evidence via MCP tools
```

## Troubleshooting

- If imports fail, reinstall editable package: `python3 -m pip install -e ".[dev]"`.
- If binary extraction is empty, verify Tika availability at `http://localhost:9998/tika`.
- If vector retrieval fails, confirm pgvector extension and schema bootstrap completed.
