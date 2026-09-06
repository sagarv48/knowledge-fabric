"""Unit tests for the reranking module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from knowledge_fabric.retrieval.models import RetrievalHit
from knowledge_fabric.reranking import (
    CohereReranker,
    CrossEncoderReranker,
    PassthroughReranker,
    build_reranker,
)


def _make_hit(chunk_id: int, score: float, text: str = "chunk text") -> RetrievalHit:
    return RetrievalHit(
        chunk_id=chunk_id,
        document_id=1,
        document_uri="doc://test",
        chunk_index=chunk_id,
        chunk_text=text,
        score=score,
        source="lexical",
    )


# ── PassthroughReranker ────────────────────────────────────────────────────


def test_passthrough_preserves_order():
    reranker = PassthroughReranker()
    hits = [_make_hit(i, float(10 - i)) for i in range(5)]
    result = reranker.rerank("query", hits, top_n=3)
    assert len(result) == 3
    assert [h.chunk_id for h in result] == [0, 1, 2]


def test_passthrough_empty_hits():
    reranker = PassthroughReranker()
    assert reranker.rerank("query", [], top_n=5) == []


# ── CrossEncoderReranker ────────────────────────────────────────────────────


def test_cross_encoder_raises_import_error_without_package():
    reranker = CrossEncoderReranker()
    with patch.dict("sys.modules", {"sentence_transformers": None}):
        with pytest.raises(ImportError, match="sentence-transformers is required"):
            reranker.rerank("query", [_make_hit(1, 0.5)], top_n=1)


def test_cross_encoder_reranks_by_model_scores():
    hits = [_make_hit(i, float(i)) for i in range(3)]

    mock_model = MagicMock()
    import numpy as np
    # Model says: hit[2] is best, hit[0] next, hit[1] worst
    mock_model.predict.return_value = np.array([0.5, 0.1, 0.9])

    reranker = CrossEncoderReranker()
    reranker._model = mock_model  # inject mock to bypass import

    result = reranker.rerank("query", hits, top_n=3)
    # Expected order: chunk_id 2 (score 0.9), 0 (0.5), 1 (0.1)
    assert [h.chunk_id for h in result] == [2, 0, 1]


def test_cross_encoder_from_env_reads_model_name(monkeypatch):
    monkeypatch.setenv("CROSS_ENCODER_MODEL", "cross-encoder/test-model")
    reranker = CrossEncoderReranker.from_env()
    assert reranker._model_name == "cross-encoder/test-model"


# ── CohereReranker ─────────────────────────────────────────────────────────


def test_cohere_reranker_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("COHERE_API_KEY", raising=False)
    with pytest.raises(EnvironmentError, match="COHERE_API_KEY is required"):
        CohereReranker.from_env()


def test_cohere_reranker_empty_hits():
    reranker = CohereReranker(_api_key="test-key", _model="rerank-english-v3.0")
    assert reranker.rerank("query", [], top_n=5) == []


def test_cohere_reranker_calls_api_and_reorders():
    import json
    hits = [_make_hit(i, float(i), text=f"text {i}") for i in range(3)]
    reranker = CohereReranker(_api_key="test-key", _model="rerank-english-v3.0")

    mock_response_data = {
        "results": [
            {"index": 2, "relevance_score": 0.95},
            {"index": 0, "relevance_score": 0.7},
            {"index": 1, "relevance_score": 0.3},
        ]
    }

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.read.return_value = json.dumps(mock_response_data).encode()

    with patch("urllib.request.urlopen", return_value=mock_response):
        result = reranker.rerank("query", hits, top_n=3)

    assert len(result) == 3
    assert result[0].chunk_id == 2
    assert result[0].score == pytest.approx(0.95)
    assert "reranked_cohere" in result[0].source


# ── build_reranker factory ──────────────────────────────────────────────────


def test_build_reranker_passthrough_by_default(monkeypatch):
    monkeypatch.delenv("RERANKER", raising=False)
    reranker = build_reranker()
    assert isinstance(reranker, PassthroughReranker)


def test_build_reranker_cross_encoder(monkeypatch):
    monkeypatch.setenv("RERANKER", "cross_encoder")
    reranker = build_reranker()
    assert isinstance(reranker, CrossEncoderReranker)


def test_build_reranker_cohere(monkeypatch):
    monkeypatch.setenv("RERANKER", "cohere")
    monkeypatch.setenv("COHERE_API_KEY", "test-key")
    reranker = build_reranker()
    assert isinstance(reranker, CohereReranker)


def test_build_reranker_none_explicit(monkeypatch):
    monkeypatch.setenv("RERANKER", "none")
    reranker = build_reranker()
    assert isinstance(reranker, PassthroughReranker)
