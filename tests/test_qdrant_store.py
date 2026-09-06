"""Unit tests for pluggable retrieval store and Qdrant store adapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from knowledge_fabric.retrieval.models import RetrievalHit
from knowledge_fabric.retrieval.qdrant import QdrantRetrievalStore
from knowledge_fabric.retrieval.store import build_retrieval_store


def test_qdrant_store_vector_search() -> None:
    store = QdrantRetrievalStore(url="http://localhost:6333", collection="test_docs")

    mock_response = {
        "result": [
            {
                "id": 101,
                "score": 0.92,
                "payload": {
                    "document_uri": "s3://bucket/doc.pdf",
                    "chunk_text": "Emergency access requires CISO signoff.",
                    "source_type": "pdf",
                    "metadata": {"tenant_id": "corp_a"},
                },
            }
        ]
    }

    with patch.object(store, "_request", return_value=mock_response) as mock_req:
        hits = store.vector_search(
            query_vector=[0.1, 0.2, 0.3],
            top_k=5,
            tenant_id="corp_a",
        )

        assert len(hits) == 1
        assert hits[0].chunk_id == 101
        assert hits[0].score == 0.92
        assert "Emergency access" in hits[0].snippet

        # Verify filter was included in payload
        _, kwargs = mock_req.call_args
        payload = kwargs["payload"]
        assert payload["filter"]["must"][0] == {"key": "tenant_id", "match": {"value": "corp_a"}}


def test_qdrant_store_health_check() -> None:
    store = QdrantRetrievalStore(url="http://localhost:6333", collection="test_docs")

    mock_resp = {"result": {"status": "green", "vectors_count": 50000000}}
    with patch.object(store, "_request", return_value=mock_resp):
        res = store.health_check()
        assert res["backend"] == "qdrant"
        assert res["status"] == "connected"
        assert res["vectors_count"] == 50000000


def test_build_retrieval_store_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    # Test qdrant factory
    monkeypatch.setenv("RETRIEVAL_STORE_BACKEND", "qdrant")
    monkeypatch.setenv("QDRANT_URL", "http://qdrant-cluster:6333")
    store = build_retrieval_store()
    assert isinstance(store, QdrantRetrievalStore)
    assert store.url == "http://qdrant-cluster:6333"

    # Test invalid backend raises ValueError
    with pytest.raises(ValueError, match="Unsupported retrieval backend"):
        build_retrieval_store(backend="unsupported_db")
