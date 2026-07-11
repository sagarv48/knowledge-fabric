# Cleanup Prompt: Remove Acme-Specific Content from Open Source Repos

Use this prompt in the current repo if it still contains Acme/workflow-specific wording and you want to convert it to vendor-neutral Knowledge Fabric.

```text
Refactor this repository into a vendor-neutral open-source project named Knowledge Fabric.

Remove or move to private/future docs all references to:
- Acme
- Acme Infinity
- Acme MCP
- Acme case types
- Acme workflows
- AKF private content
- OAuth details for Acme
- Workflow Broker
- Workflow execution
- Case creation
- Assignment completion
- Audit lineage tied to workflow execution

Replace with vendor-neutral terms:
- Knowledge Fabric
- evidence retrieval
- hybrid retrieval
- source adapters
- evidence package
- retrieval evaluation
- MCP retrieval server

Allowed references:
- Acme may appear only in docs that explicitly say "private adapter example" or "Phase 3 enterprise integration".
- No internal/proprietary content should remain in open-source docs.

Update:
- README.md
- docs/*
- prompts/*
- config examples

Create a summary listing:
1. Files modified
2. Acme-specific content removed
3. Content moved to private Phase 3 docs
4. Remaining vendor-specific terms, if any
```
```
