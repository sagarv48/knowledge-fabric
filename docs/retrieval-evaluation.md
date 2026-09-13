# Retrieval Evaluation and Quality Gates

Knowledge Fabric provides an automated offline evaluation suite and quality gate framework to measure relevance across lexical, vector, and hybrid retrieval strategies, preventing silent retrieval regressions as schemas and datasets evolve.

---

## 1. Evaluation Objectives

1. **Relevance Truthfulness:** Make retrieval quality quantifiable, repeatable, and verifiable without subjective guesswork.
2. **Strategy Attribution:** Compare lexical-only, vector-only, and hybrid RRF strategies side-by-side on identical queries.
3. **Category Dissection:** Evaluate specific failure modes across exact terminology, paraphrases, dense/sparse disagreement, metadata constraints, and unanswerable queries.
4. **CI Quality Gates:** Block pull requests or configuration changes that regress retrieval metrics below configurable quality thresholds.

---

## 2. Evaluation Dataset Specification

Evaluation datasets are versioned YAML files adhering to the following schema:

```yaml
version: "1.0.0"
dataset_id: "knowledge-fabric-seed-eval-v1"
license: "Apache-2.0"
provenance: "Curated Knowledge Fabric technical corpus covering RRF, data models, evidence packaging, MCP tools, and storage backends."

corpus:
  - id: 101
    document_uri: "docs/architecture.md"
    source_type: "markdown"
    text: "Reciprocal Rank Fusion (RRF) combines rankings from multiple retrieval legs..."

queries:
  - id: "q-exact-01"
    category: "exact"
    text: "Reciprocal Rank Fusion rrf_k"
    relevant_chunk_ids: [101, 102]
    expected_document_uris: ["docs/architecture.md"]
    description: "Exact technical term query testing lexical match for RRF algorithm parameter"

  - id: "q-unanswerable-01"
    category: "unanswerable"
    text: "quantum computing superconductor qubit Josephson junction fabrication"
    relevant_chunk_ids: []
    description: "Out of domain negative query: zero relevant chunks exist"
```

### Query Categories

| Category | Purpose | Expected Behavior |
| :--- | :--- | :--- |
| `exact` | Technical terms, symbols, function names, exact keywords | Lexical full-text search excels; high Precision@5 and MRR. |
| `paraphrase` | Conceptual questions, multi-word paraphrases, intent-based queries | Vector semantic embeddings capture conceptual similarity where exact keywords differ. |
| `disagreement` | Queries where lexical keywords and vector embeddings yield divergent candidate sets | Hybrid RRF merges both perspectives, balancing rank signals. |
| `metadata` | Queries constrained by `source_type` or metadata filters | Validates pre- or post-filtering selectivity without data leakage. |
| `unanswerable` | Out-of-domain or nonexistent topics | Evaluates whether the system refrains from returning hallucinated or false-positive hits (`No-Result Accuracy`). |

---

## 3. Metrics

Knowledge Fabric calculates standard information retrieval (IR) and observability metrics:

| Metric | Definition | Range | Target |
| :--- | :--- | :---: | :---: |
| **Recall@10** | Proportion of relevant items retrieved in top 10 ($\frac{\| \text{Relevant} \cap \text{Top10} \|}{\| \text{Relevant} \|}$) | $[0.0, 1.0]$ | $\ge 0.80$ |
| **Precision@5** | Proportion of top 5 returned items that are relevant ($\frac{\| \text{Relevant} \cap \text{Top5} \|}{5}$) | $[0.0, 1.0]$ | $\ge 0.30$ |
| **MRR** | Mean Reciprocal Rank of the first relevant result ($\frac{1}{\text{rank}_1}$) | $[0.0, 1.0]$ | $\ge 0.60$ |
| **NDCG@10** | Normalized Discounted Cumulative Gain at rank 10, weighting higher ranks | $[0.0, 1.0]$ | $\ge 0.70$ |
| **No-Result Accuracy** | Proportion of unanswerable queries where zero false-positive chunks were returned | $[0.0, 1.0]$ | $1.00$ |
| **Avg Latency** | Mean query execution time in milliseconds | $\ge 0.0$ ms | $< 50$ ms |
| **P95 Latency** | 95th-percentile query execution latency | $\ge 0.0$ ms | $< 100$ ms |

---

## 4. Running Evaluations

### Command-Line Interface (`knowledge-fabric-eval`)

The evaluation runner is installed as an executable CLI tool:

```bash
# Run baseline evaluation across lexical, vector, and hybrid modes
knowledge-fabric-eval

# Generate machine-readable JSON and human-readable Markdown reports
knowledge-fabric-eval \
  --dataset src/knowledge_fabric/evaluation/queries.yaml \
  --output-markdown docs/evaluation/baseline_report.md \
  --output-json docs/evaluation/baseline_report.json

# Enforce quality gates (exits with non-zero code on failure)
knowledge-fabric-eval \
  --threshold-mrr 0.50 \
  --threshold-recall 0.75 \
  --threshold-ndcg 0.60
```

### Python API

You can also run evaluations programmatically:

```python
from knowledge_fabric.evaluation import (
    RetrievalEvaluationRunner,
    create_seed_pipeline,
    load_dataset,
    make_pipeline_retriever,
)

# Load dataset
metadata, queries = load_dataset("src/knowledge_fabric/evaluation/queries.yaml")

# Instantiate pipeline & retriever adapter
pipeline = create_seed_pipeline()
retriever = make_pipeline_retriever(pipeline)

# Run evaluation
runner = RetrievalEvaluationRunner(retriever, dataset_id=metadata["dataset_id"])
report = runner.evaluate(queries=queries, modes=("lexical", "vector", "hybrid"))

# Check quality gates
passed = report.check_quality_gates(min_mrr=0.50, min_recall=0.75)
print(f"Quality gate passed: {passed}")

# Export reports
print(report.to_markdown())
```

---

## 5. Quality Gate Guidelines

When establishing CI gates:
1. **Never gate on synthetic vectors:** Ensure production quality gates run against actual embedding models (e.g. `nomic-embed-text` via Ollama, or OpenAI `text-embedding-3-small`), not `MockEmbeddingProvider`.
2. **Track drift over time:** Store timestamped reports in `docs/evaluation/reports/` to detect relevance regressions after re-chunking, re-indexing, or prompt changes.
3. **Analyze Disagreements:** Use `report.per_query_results` to inspect queries where hybrid underperforms lexical or vector to tune RRF weights (`lexical_weight`, `vector_weight`, `rrf_k`).
