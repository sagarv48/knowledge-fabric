"""Tests for evaluation and benchmark ranking metrics."""

from __future__ import annotations

import pytest

from benchmarks.evaluate_retrieval import dcg_at_k, mrr_at_k, ndcg_at_k, recall_at_k


def test_mrr_at_k_first_hit() -> None:
    ground_truth = {"doc_1": 2, "doc_2": 1}
    assert mrr_at_k(["doc_1", "doc_3", "doc_4"], ground_truth) == 1.0
    assert mrr_at_k(["doc_3", "doc_1", "doc_4"], ground_truth) == 0.5
    assert mrr_at_k(["doc_3", "doc_4", "doc_5"], ground_truth) == 0.0


def test_recall_at_k() -> None:
    ground_truth = {"doc_1": 1, "doc_2": 1, "doc_3": 1}
    assert recall_at_k(["doc_1", "doc_2"], ground_truth, k=2) == pytest.approx(2 / 3)
    assert recall_at_k(["doc_1", "doc_2", "doc_3"], ground_truth, k=5) == 1.0
    assert recall_at_k(["doc_4", "doc_5"], ground_truth, k=2) == 0.0


def test_ndcg_at_k_ideal() -> None:
    ground_truth = {"doc_1": 2, "doc_2": 1}
    # Perfect ranking: highest relevance first
    perfect = ["doc_1", "doc_2", "doc_3"]
    assert ndcg_at_k(perfect, ground_truth, k=3) == pytest.approx(1.0)

    # Suboptimal ranking: lower relevance first
    suboptimal = ["doc_2", "doc_1", "doc_3"]
    score = ndcg_at_k(suboptimal, ground_truth, k=3)
    assert 0.0 < score < 1.0


def test_ndcg_at_k_empty_ground_truth() -> None:
    assert ndcg_at_k(["doc_1"], {}, k=3) == 0.0
