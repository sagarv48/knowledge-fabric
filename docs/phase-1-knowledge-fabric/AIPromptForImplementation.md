# AI Prompt for Phase 1 Implementation: Knowledge Fabric

Use this prompt with Copilot CLI or another coding agent from the `knowledge-fabric` repo root.

```text
You are implementing Phase 1: Knowledge Fabric.

Goal:
Build a vendor-neutral evidence retrieval platform. This project must not contain product-specific references, workflow execution, approvals, case creation, or runtime enterprise actions.

Hard constraints:
- Do not add product-specific integration.
- Do not add workflow execution.
- Do not add approval flows.
- Do not hardcode model names.
- Keep embedding providers configurable.
- The MCP server must return evidence, not final answers.

Implement in this order:

1. Create Python project structure under src/knowledge_fabric.
2. Add docker-compose.yml for PostgreSQL + pgvector and Apache Tika.
3. Create config/settings.yaml with configurable providers.
4. Add database schema for documents, chunks, retrieval_runs, and audit_events.
5. Implement document ingestion for md, txt, html, pdf, docx, and pptx.
6. Use Apache Tika for binary document extraction.
7. Implement heading-aware chunking with fallback size-based chunking.
8. Implement EmbeddingProvider interface with a placeholder/mock provider first.
9. Implement lexical retrieval using PostgreSQL full-text search.
10. Implement vector retrieval using pgvector.
11. Implement RRF fusion for hybrid retrieval.
12. Implement evidence package model.
13. Implement MCP server with tools:
    - retrieve_evidence
    - get_document
    - explain_retrieval
14. Implement audit logging for every retrieval call.
15. Add evaluation query YAML.
16. Add evaluation runner comparing lexical, vector, and hybrid.
17. Add README and setup instructions.

Acceptance criteria:
- `retrieve_evidence` returns JSON evidence packages.
- Hybrid retrieval combines lexical and vector results.
- No product-specific terms appear in source code or docs except in examples clearly marked as external/private adapter examples.
- No workflow execution functions exist in this repo.
```
```

## Manual actions after AI implementation

```bash
git status
git diff
docker compose up -d
pytest
```

Commit:

```bash
git add .
git commit -m "Implement Knowledge Fabric retrieval MVP scaffold"
```
