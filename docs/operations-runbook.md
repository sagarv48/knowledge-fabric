# Knowledge Fabric: Operations & Observability Runbook

This runbook documents operational procedures for administering, monitoring, backing up, and maintaining Knowledge Fabric deployments.

---

## 1. System Health & Diagnostics

### FastMCP Health Check Tool
AI agents and administrators can query server runtime configuration via the `health_check` MCP tool or CLI:
```json
{
  "status": "ok",
  "embedding_provider": "OllamaEmbeddingProvider",
  "embedding_dimension": 768,
  "db_status": "connected",
  "db_latency_ms": 3,
  "document_count": 1420,
  "chunk_count": 5680,
  "dimension_check": "match"
}
```

### Index Status & Distribution Inspection
Inspect document distribution across source formats and namespaces:
```bash
# Using Knowledge Fabric Ingestion CLI
knowledge-fabric-ingest --index-status --tenant acme-corp

# Or query via MCP tool:
# get_index_status(tenant_id="acme-corp")
```

Example response:
```json
{
  "tenant_id": "acme-corp",
  "total_documents": 250,
  "total_chunks": 1024,
  "sources": [
    {"source_type": "markdown", "document_count": 180, "chunk_count": 720, "last_indexed_at": "2026-09-13T10:00:00"},
    {"source_type": "pdf", "document_count": 70, "chunk_count": 304, "last_indexed_at": "2026-09-13T10:15:00"}
  ],
  "storage_backend": "postgres"
}
```

---

## 2. Database Consistency Verification

Knowledge Fabric enforces relational integrity with automated audits to detect orphaned records, dimension mismatches, and data boundary violations.

Run consistency check:
```bash
knowledge-fabric-ingest --check-consistency --tenant default
```

Audited invariants:
- **Orphaned Chunks:** Chunks referencing missing `document_id`.
- **Empty Documents:** Documents with 0 associated chunks.
- **Null Tenant IDs:** Documents lacking explicit tenant namespace attribution.
- **Null Embeddings:** Chunks where dense vectors are unpopulated.

Exit code is `0` if healthy, `1` if anomalies are detected.

---

## 3. Re-Embedding and Model Migration

When upgrading or changing embedding models (e.g. migrating from 384-dimension to 768-dimension embeddings):

1. Update `config/settings.yaml` (or set `EMBEDDING_PROVIDER` and `EMBEDDING_DIMENSION` environment variables).
2. Run in-place re-embedding without re-parsing raw source files:
   ```bash
   knowledge-fabric-ingest --reembed --tenant default
   ```
3. Verify dimension alignment:
   ```bash
   knowledge-fabric-ingest --check-consistency
   ```

---

## 4. Tenant Offboarding & Secure Purge

To completely purge a customer namespace in compliance with GDPR/SOC2 deletion obligations:

```bash
# Must provide explicit --confirm flag to avoid accidental data loss
knowledge-fabric-ingest --purge-tenant acme-corp --confirm
```

This atomically deletes:
- All documents belonging to `acme-corp`.
- All cascading chunks and vector embeddings.
- Associated retrieval telemetry runs and audit event logs.

---

## 5. Backup and Restore Procedures

### Database Backup
Knowledge Fabric utilizes PostgreSQL with `pgvector` and `tsvector` columns. Standard logical dumps preserve all vector embeddings and search indexes:

```bash
# Dump entire knowledge_fabric database
pg_dump -h localhost -U postgres -d knowledge_fabric -F c -b -v -f knowledge_fabric_backup.dump
```

### Database Restore
```bash
# Restore from custom-format dump
pg_restore -h localhost -U postgres -d knowledge_fabric -v -c knowledge_fabric_backup.dump

# Validate restored database consistency
knowledge-fabric-ingest --check-consistency
```

---

## 6. Disaster Recovery & Rollback

1. **Schema Migration Rollback:** Migrations are sequentially tracked. In the event of an aborted migration, rollback using the migration runner or restore from the pre-migration snapshot.
2. **Degraded Retrieval Recovery:** If vector embeddings provider fails, Knowledge Fabric automatically degrades to `degraded_lexical` full-text search while logging warnings. Once the provider recovers (e.g. Ollama service restart), queries seamlessly resume hybrid RRF fusion.
