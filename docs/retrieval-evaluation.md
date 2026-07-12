# Retrieval Evaluation

Knowledge Fabric compares lexical, vector, and hybrid retrieval quality using standard ranking metrics.

## Evaluation modes

- **Lexical**: full-text search ranking
- **Vector**: embedding similarity ranking
- **Hybrid**: reciprocal rank fusion (RRF) of lexical + vector

## Metrics

- **Recall@10**: fraction of relevant items retrieved in top 10
- **Precision@5**: fraction of top 5 results that are relevant
- **MRR**: mean reciprocal rank of first relevant result
- **NDCG@10**: rank-aware relevance quality in top 10

## Evaluation assets

```text
Query set:
  src/knowledge_fabric/evaluation/queries.yaml

Runner:
  src/knowledge_fabric/evaluation/runner.py
```

## Evaluation flow

```text
Evaluation Queries
  ->
Retriever(mode, query, top_k)
  ->
Ranked chunk ids
  ->
Metric computation
  ->
Per-mode score report
```

## Example usage (conceptual)

```text
Load queries -> Execute lexical/vector/hybrid retrieval -> Compute Recall@10, Precision@5, MRR, NDCG@10 -> Compare modes
```

## Recommended practice

1. Establish lexical baseline first.
2. Add vector retrieval and compare.
3. Tune fusion weights for hybrid mode.
4. Track metric drift over time as sources evolve.
