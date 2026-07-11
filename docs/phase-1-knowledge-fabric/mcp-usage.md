# MCP Tool Usage

Knowledge Fabric exposes three Phase 1 MCP-style tools:

1. `retrieve_evidence(query_text, top_k=10, source_type=None, trace_id=None)`
2. `get_document(document_id=None, source_uri=None)`
3. `explain_retrieval(query_text, top_k=10, source_type=None)`

## Tool wiring

Use:

- `knowledge_fabric.retrieval.postgres.PostgresRetrievalStore`
- `knowledge_fabric.retrieval.pipeline.RetrievalPipeline`
- `knowledge_fabric.db.audit.AuditLogger`
- `knowledge_fabric.mcp.KnowledgeFabricMCPTools`

Example bootstrap is provided at:

`examples/mcp_tool_bootstrap.py`
