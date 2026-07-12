# Security and Data Boundaries

This document defines Phase 1 security posture and data boundaries for evidence retrieval.

## Boundary model

```text
Source Files
  ->
Ingestion + Chunking
  ->
PostgreSQL (documents/chunks)
  ->
Retrieval Pipeline
  ->
Evidence Package
```

## In-scope data handling

- Document text and metadata normalization
- Chunk-level storage for retrieval
- Retrieval telemetry in `retrieval_runs` and `audit_events`

## Out-of-scope actions

- Workflow execution
- Approval workflows
- Runtime enterprise actions
- Product-specific connectors

## Security guidelines

- Keep credentials out of source-controlled config values.
- Restrict database and Tika exposure to local/dev networks by default.
- Log retrieval metadata, not secrets.
- Treat source documents as potentially sensitive and apply least-access storage.

## Data minimization

- Store only metadata required for retrieval and traceability.
- Keep evidence payload limited to needed snippets and identifiers.
- Avoid coupling evidence package with environment-specific internals.

## Operational checks

1. Verify no secrets in repository before release.
2. Verify only required ports are exposed locally.
3. Verify evidence package does not include hidden private fields.
4. Verify audit logging captures retrieval events consistently.
