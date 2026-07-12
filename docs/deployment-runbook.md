# Deployment Runbook (Phase 1)

This runbook describes how to operate Knowledge Fabric Phase 1 in a local or non-production environment focused on evidence retrieval.

## 1. Environment preparation

```bash
python3 -m pip install -e ".[dev]"
docker compose up -d
```

Required services:

- PostgreSQL + pgvector
- Apache Tika

## 2. Data ingestion

Run persistent ingestion for a file or directory:

```bash
knowledge-fabric-ingest --path sources --recursive --embed
```

What it does:

```text
Read source files -> Ingest text -> Chunk content -> Optionally generate mock embeddings -> Persist documents/chunks
```

## 3. MCP server startup

```bash
knowledge-fabric-mcp
```

Registered tools:

- `retrieve_evidence`
- `get_document`
- `explain_retrieval`

## 4. Verification checks

1. Run tests:
   ```bash
   python3 -m pytest
   ```
2. Validate schema tables populated:
   - `documents`
   - `chunks`
3. Verify retrieval telemetry:
   - `retrieval_runs`
   - `audit_events`

## 5. CI controls

GitHub Actions workflow:

`/.github/workflows/ci.yml`

Runs tests on Python 3.11 and 3.12 for pushes and pull requests.

## 6. Recovery and rollback

- Stop services: `docker compose down`
- Reset local DB state (destructive): `docker compose down -v`
- Restart clean: `docker compose up -d`

## 7. Operational boundaries

- Evidence retrieval only
- No workflow execution
- No approval flows
- No runtime enterprise action connectors
