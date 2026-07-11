"""Evaluation runner for lexical, vector, and hybrid retrieval."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yaml

RetrieverFn = Callable[[str, str, int], list[int]]


@dataclass(slots=True)
class EvaluationQuery:
    id: str
    text: str
    relevant_chunk_ids: list[int]


@dataclass(slots=True)
class ModeMetrics:
    mode: str
    recall_at_10: float
    precision_at_5: float
    mrr: float
    ndcg_at_10: float


class RetrievalEvaluationRunner:
    """Computes retrieval metrics for each retrieval mode."""

    def __init__(self, retriever_fn: RetrieverFn) -> None:
        self._retriever_fn = retriever_fn

    def evaluate(
        self,
        *,
        queries: list[EvaluationQuery],
        modes: tuple[str, ...] = ("lexical", "vector", "hybrid"),
    ) -> dict[str, ModeMetrics]:
        by_mode: dict[str, ModeMetrics] = {}
        for mode in modes:
            recall_values: list[float] = []
            precision_values: list[float] = []
            mrr_values: list[float] = []
            ndcg_values: list[float] = []

            for query in queries:
                ranked = self._retriever_fn(mode, query.text, 10)
                relevant = set(query.relevant_chunk_ids)
                recall_values.append(recall_at_k(ranked, relevant, k=10))
                precision_values.append(precision_at_k(ranked, relevant, k=5))
                mrr_values.append(mean_reciprocal_rank(ranked, relevant))
                ndcg_values.append(ndcg_at_k(ranked, relevant, k=10))

            by_mode[mode] = ModeMetrics(
                mode=mode,
                recall_at_10=_avg(recall_values),
                precision_at_5=_avg(precision_values),
                mrr=_avg(mrr_values),
                ndcg_at_10=_avg(ndcg_values),
            )
        return by_mode


def load_queries(path: str | Path) -> list[EvaluationQuery]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    queries = raw.get("queries", [])
    return [
        EvaluationQuery(
            id=str(item["id"]),
            text=str(item["text"]),
            relevant_chunk_ids=[int(chunk_id) for chunk_id in item.get("relevant_chunk_ids", [])],
        )
        for item in queries
    ]


def recall_at_k(ranked_ids: list[int], relevant: set[int], *, k: int) -> float:
    if not relevant:
        return 0.0
    top = ranked_ids[:k]
    found = sum(1 for chunk_id in top if chunk_id in relevant)
    return found / len(relevant)


def precision_at_k(ranked_ids: list[int], relevant: set[int], *, k: int) -> float:
    if k <= 0:
        return 0.0
    top = ranked_ids[:k]
    if not top:
        return 0.0
    found = sum(1 for chunk_id in top if chunk_id in relevant)
    return found / k


def mean_reciprocal_rank(ranked_ids: list[int], relevant: set[int]) -> float:
    for index, chunk_id in enumerate(ranked_ids, start=1):
        if chunk_id in relevant:
            return 1.0 / index
    return 0.0


def ndcg_at_k(ranked_ids: list[int], relevant: set[int], *, k: int) -> float:
    top = ranked_ids[:k]
    dcg = 0.0
    for index, chunk_id in enumerate(top, start=1):
        gain = 1.0 if chunk_id in relevant else 0.0
        dcg += gain / math.log2(index + 1)

    ideal_hits = min(k, len(relevant))
    if ideal_hits == 0:
        return 0.0
    idcg = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_hits + 1))
    return dcg / idcg


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
