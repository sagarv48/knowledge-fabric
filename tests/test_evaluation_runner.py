from __future__ import annotations

from pathlib import Path

from knowledge_fabric.evaluation import (
    RetrievalEvaluationRunner,
    load_queries,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_metric_functions() -> None:
    ranked = [3, 1, 9, 7, 5]
    relevant = {1, 5}

    assert recall_at_k(ranked, relevant, k=3) == 0.5
    assert precision_at_k(ranked, relevant, k=5) == 0.4
    assert mean_reciprocal_rank(ranked, relevant) == 0.5
    assert 0.0 <= ndcg_at_k(ranked, relevant, k=5) <= 1.0


def test_load_queries_from_yaml(tmp_path: Path) -> None:
    yaml_file = tmp_path / "queries.yaml"
    yaml_file.write_text(
        """
queries:
  - id: q1
    text: sample
    relevant_chunk_ids: [1, 2]
""".strip(),
        encoding="utf-8",
    )
    queries = load_queries(yaml_file)
    assert len(queries) == 1
    assert queries[0].id == "q1"
    assert queries[0].relevant_chunk_ids == [1, 2]


def test_evaluation_runner_modes() -> None:
    queries = load_queries("src/knowledge_fabric/evaluation/queries.yaml")

    def _retriever(mode: str, query: str, top_k: int) -> list[int]:
        if mode == "lexical":
            return [101, 202, 999]
        if mode == "vector":
            return [202, 888, 777]
        return [101, 202, 301]

    runner = RetrievalEvaluationRunner(_retriever)
    report = runner.evaluate(queries=queries)

    assert set(report.keys()) == {"lexical", "vector", "hybrid"}
    assert all(0.0 <= metrics.recall_at_10 <= 1.0 for metrics in report.values())
