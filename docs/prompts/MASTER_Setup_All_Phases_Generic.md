# Master Setup Prompt for All Phases (Generic)

Use this prompt at the beginning of a new AI coding session.

```text
We are separating the project into three phases:

Phase 1: Knowledge Fabric
- Vendor-neutral evidence retrieval platform.
- Ingestion, chunking, embeddings, lexical retrieval, vector retrieval, hybrid retrieval, evidence packaging, MCP retrieval, evaluation.
- No workflow execution.

Phase 2: Intent Fabric
- Vendor-neutral intent planning and approval framework.
- Consumes Knowledge Fabric evidence packages.
- Produces plans, action contracts, policy decisions, and approval packages.
- Simulation only. No real runtime execution.

Phase 3: Enterprise Integration
- Runtime adapters, product integrations, and deployment examples.
- Managed as private enterprise material outside this repository.

When working on a phase, do not contaminate it with concepts from later phases.
If working on Phase 1, do not add Phase 2 or Phase 3 functionality.
If working on Phase 2, depend only on the evidence package contract from Phase 1.
```
