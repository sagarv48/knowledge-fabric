# Master Setup Prompt for All Phases

Use this prompt at the beginning of a new AI coding session.

```text
We are separating the project into three phases and repositories:

Phase 1: knowledge-fabric
- Open-source vendor-neutral evidence retrieval platform.
- Ingestion, chunking, embeddings, lexical retrieval, vector retrieval, hybrid RRF, evidence packages, MCP retrieval API, evaluation.
- No workflow execution.
- No Acme.

Phase 2: intent-fabric
- Vendor-neutral intent planning and approval framework.
- Consumes Knowledge Fabric evidence packages.
- Produces plans, action contracts, policy decisions, and approval packages.
- Simulation only. No real runtime execution.
- No Acme.

Phase 3: knowledge-fabric-Acme or enterprise-integration-private
- Private repository.
- Contains Acme/private enterprise source adapters and runtime integration.
- May connect to Acme MCP and private knowledge sources.
- Must not be open-source.

When working on a phase, do not contaminate it with concepts from later phases.
If working on Phase 1, do not add Phase 2 or Phase 3 functionality.
If working on Phase 2, depend only on the evidence package contract from Phase 1.
If working on Phase 3, keep all enterprise-specific details private.
```
```
