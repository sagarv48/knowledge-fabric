# Knowledge Fabric, Intent Fabric, and Enterprise Integration

This documentation package separates three related but independent initiatives:

1. **Phase 1: Knowledge Fabric**  
   Open-source, vendor-neutral retrieval platform. It ingests documents, chunks them, indexes them for lexical/vector search, performs hybrid retrieval, and returns evidence packages through MCP.

2. **Phase 2: Intent Fabric**  
   Open-source or separately governed planning layer. It converts user intent and evidence into structured plans, action contracts, approvals, and simulated execution. It does not include vendor-specific runtime integrations.

3. **Phase 3: Enterprise / Acme Integration**  
   Private integration layer. It connects Knowledge Fabric and Intent Fabric to Acme-specific sources, AKF content, Acme docs, Acme MCP, runtime deployment, and enterprise authentication.

## Recommended repository strategy

Use separate repositories:

```text
knowledge-fabric              # public/open-source retrieval platform
intent-fabric                 # public/open-source planning and approval framework, optional separate project
knowledge-fabric-Acme         # private enterprise/Acme-specific adapters and deployment
```

Avoid Git submodules unless you have a strict versioning reason. For most development, separate repos with package dependencies are cleaner.

## Dependency direction

```text
knowledge-fabric
      ↓
intent-fabric
      ↓
enterprise-integration-adapters
```

Knowledge Fabric must not depend on Intent Fabric or Acme.
Intent Fabric may consume Knowledge Fabric evidence packages.
Acme integration may consume both.

## What must remain vendor-neutral

- Ingestion interfaces
- Chunking
- Embedding provider abstraction
- Lexical search
- Vector search
- Hybrid retrieval
- RRF fusion
- Evidence package contract
- MCP retrieval tools
- Evaluation framework

## What must remain private / enterprise-specific

- Acme internal documents
- AKF internal docs
- Acme MCP runtime details
- Acme URLs, OAuth credentials, case types, rule names if not public
- Internal architecture diagrams
- Internal security reviews
- Customer or production data
