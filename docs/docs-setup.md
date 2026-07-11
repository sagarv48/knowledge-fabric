# Phase 1 Documentation Setup

Create these docs in the `knowledge-fabric` repo:

```text
docs/architecture.md
docs/local-setup.md
docs/evidence-package-contract.md
docs/retrieval-evaluation.md
docs/model-provider-strategy.md
docs/security-and-data-boundaries.md
```

## Prompt to generate docs

```text
Create vendor-neutral documentation for Knowledge Fabric.

Generate these files:

1. docs/architecture.md
2. docs/local-setup.md
3. docs/evidence-package-contract.md
4. docs/retrieval-evaluation.md
5. docs/model-provider-strategy.md
6. docs/security-and-data-boundaries.md

Requirements:
- No Acme-specific content.
- No workflow execution content.
- Focus on evidence retrieval.
- Include diagrams using plain markdown text blocks.
- Include local setup using PostgreSQL + pgvector + Apache Tika.
- Include evaluation metrics: Recall@10, Precision@5, MRR, NDCG@10.
```
```
