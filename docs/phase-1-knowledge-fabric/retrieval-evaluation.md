# Retrieval Evaluation

Phase 1 includes a retrieval evaluation runner with mode comparison across:

- lexical
- vector
- hybrid

## Query set

Default query set:

`src/knowledge_fabric/evaluation/queries.yaml`

Each entry contains:

- `id`
- `text`
- `relevant_chunk_ids`

## Runner

Use `knowledge_fabric.evaluation.RetrievalEvaluationRunner` with a retriever callback:

`retriever_fn(mode, query_text, top_k) -> list[int]`

Metrics produced:

- Recall@10
- Precision@5
- MRR
- NDCG@10
