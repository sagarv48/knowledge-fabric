# Retrieval Evaluation Report: `knowledge-fabric-seed-eval-v1` (v1.0.0)

- **Generated At:** 2026-09-13T09:04:39.369682+00:00
- **Quality Gate:** PASSED
- **System Info:**
  - `dataset_provenance`: Knowledge Fabric official benchmark query suite covering technical architecture, data contracts, and search modes
  - `pipeline`: RetrievalPipeline (InMemoryEvaluationStore + MockEmbeddingProvider)
  - `modes_evaluated`: ['lexical', 'vector', 'hybrid']
  - `top_k`: 10

## Summary Metrics Across Modes

| Mode | Recall@10 | Precision@5 | MRR | NDCG@10 | No-Result Acc | Avg Latency (ms) | P95 Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `lexical` | 0.955 | 0.291 | 0.806 | 0.806 | 1.000 | 0.1 | 0.1 |
| `vector` | 1.000 | 0.182 | 0.374 | 0.547 | 0.000 | 0.0 | 0.1 |
| `hybrid` | 1.000 | 0.291 | 0.582 | 0.684 | 0.000 | 0.1 | 0.1 |

## Category Breakdown

| Mode | Category | Queries | Recall@10 | Precision@5 | MRR | NDCG@10 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `lexical` | `exact` | 5 | 0.900 | 0.280 | 1.000 | 0.923 |
| `lexical` | `paraphrase` | 3 | 1.000 | 0.333 | 0.778 | 0.766 |
| `lexical` | `disagreement` | 2 | 1.000 | 0.300 | 0.667 | 0.785 |
| `lexical` | `metadata` | 1 | 1.000 | 0.200 | 0.200 | 0.387 |
| `lexical` | `unanswerable` | 2 | 0.000 | 0.000 | 0.000 | 0.000 |
| `vector` | `exact` | 5 | 1.000 | 0.240 | 0.429 | 0.596 |
| `vector` | `paraphrase` | 3 | 1.000 | 0.200 | 0.225 | 0.439 |
| `vector` | `disagreement` | 2 | 1.000 | 0.000 | 0.146 | 0.359 |
| `vector` | `metadata` | 1 | 1.000 | 0.200 | 1.000 | 1.000 |
| `vector` | `unanswerable` | 2 | 0.000 | 0.000 | 0.000 | 0.000 |
| `hybrid` | `exact` | 5 | 1.000 | 0.320 | 0.840 | 0.853 |
| `hybrid` | `paraphrase` | 3 | 1.000 | 0.267 | 0.344 | 0.521 |
| `hybrid` | `disagreement` | 2 | 1.000 | 0.300 | 0.333 | 0.535 |
| `hybrid` | `metadata` | 1 | 1.000 | 0.200 | 0.500 | 0.631 |
| `hybrid` | `unanswerable` | 2 | 0.000 | 0.000 | 0.000 | 0.000 |
