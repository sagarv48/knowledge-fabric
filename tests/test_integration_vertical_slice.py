"""Integration tests for the complete vertical slice.

Proves the end-to-end path:
  Mock connection factory → RetrievalPipeline → KnowledgeFabricMCPTools → EvidencePackage

No real PostgreSQL required — realistic fake rows are returned from mock cursors.
Cross-tenant isolation is validated as a negative test.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from knowledge_fabric.embeddings import MockEmbeddingProvider
from knowledge_fabric.mcp.tools import KnowledgeFabricMCPTools
from knowledge_fabric.reranking import PassthroughReranker
from knowledge_fabric.retrieval.pipeline import RetrievalPipeline
from knowledge_fabric.retrieval.postgres import PostgresRetrievalStore


# ---------------------------------------------------------------------------
# Realistic fake DB rows
# ---------------------------------------------------------------------------

_CHUNK_ROW = (
    1,       # id (chunk)
    10,      # document_id
    "file://docs/runbook.md",
    0,       # chunk_index
    "On-call engineers should escalate within 15 minutes.",
    {"tenant_id": "team-alpha"},
    0.85,    # score
)

_SOURCE_ROW = ("markdown", 3)


# ---------------------------------------------------------------------------
# Helper: build a minimal cursor that returns a fixed row list
# ---------------------------------------------------------------------------

def _make_cursor(rows: list[tuple[Any, ...]]) -> MagicMock:
    cursor = MagicMock()
    cursor.fetchall.return_value = rows
    cursor.fetchone.return_value = rows[0] if rows else None
    cursor.__enter__ = lambda s: s
    cursor.__exit__ = MagicMock(return_value=False)
    return cursor


def _make_conn(cursor: MagicMock) -> MagicMock:
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_vertical_slice_retrieve_evidence_returns_evidence_package() -> None:
    """retrieve_evidence must return a structured EvidencePackage dict."""
    cursor = _make_cursor([_CHUNK_ROW])
    conn = _make_conn(cursor)

    store = PostgresRetrievalStore(connection_factory=lambda: conn)
    provider = MockEmbeddingProvider(_dimension=8)
    pipeline = RetrievalPipeline(
        retrieval_store=store,
        embedding_provider=provider,
        reranker=PassthroughReranker(),
    )
    tools = KnowledgeFabricMCPTools(
        retrieval_pipeline=pipeline,
        retrieval_store=store,
        embedding_provider=provider,
        connection_factory=lambda: conn,
    )

    result = tools.retrieve_evidence(
        query_text="on-call escalation policy",
        top_k=5,
        tenant_id="team-alpha",
    )

    assert "query_text" in result, "EvidencePackage must contain query_text"
    assert "items" in result, "EvidencePackage must contain items"
    assert isinstance(result["items"], list)
    assert "retrieval_summary" in result, "EvidencePackage must contain retrieval_summary"
    summary = result["retrieval_summary"]
    assert summary["strategy"] == "hybrid"
    assert summary["requested_mode"] == "hybrid"
    assert summary["is_degraded"] is False
    assert "legs" in summary
    assert summary["legs"]["lexical"]["status"] == "ok"
    assert summary["legs"]["vector"]["status"] == "ok"



def test_vertical_slice_list_sources_is_tenant_scoped() -> None:
    """list_sources must delegate to list_sources_for_tenant on the store."""
    received: dict[str, Any] = {}

    class _TrackingStore:
        def lexical_search(self, *a, **kw): return []

        def vector_search(self, *a, **kw): return []

        def list_sources_for_tenant(self, tenant_id=None):
            received["tenant_id"] = tenant_id
            return [_SOURCE_ROW]

        def get_document(self, *, document_id=None, source_uri=None, tenant_id=None):
            return None

    store = _TrackingStore()
    provider = MockEmbeddingProvider(_dimension=8)
    pipeline = RetrievalPipeline(retrieval_store=store, embedding_provider=provider)  # type: ignore[arg-type]
    tools = KnowledgeFabricMCPTools(
        retrieval_pipeline=pipeline,
        retrieval_store=store,  # type: ignore[arg-type]
        embedding_provider=provider,
        connection_factory=lambda: None,
    )

    result = tools.list_sources(tenant_id="team-alpha")

    assert received["tenant_id"] == "team-alpha", "tenant_id must be forwarded to store"
    assert result["total_source_types"] == 1
    assert result["sources"][0]["source_type"] == "markdown"


def test_vertical_slice_get_document_returns_none_for_wrong_tenant() -> None:
    """get_document with a wrong tenant_id must return None (cross-tenant isolation)."""

    class _IsolatingStore:
        def lexical_search(self, *a, **kw): return []

        def vector_search(self, *a, **kw): return []

        def list_sources_for_tenant(self, tenant_id=None): return []

        def get_document(self, *, document_id=None, source_uri=None, tenant_id=None):
            # Simulate DB rejecting cross-tenant lookup
            if tenant_id == "team-beta":
                return None
            return {"id": document_id, "source_uri": "file://docs/runbook.md"}

    store = _IsolatingStore()
    provider = MockEmbeddingProvider(_dimension=8)
    pipeline = RetrievalPipeline(retrieval_store=store, embedding_provider=provider)  # type: ignore[arg-type]
    tools = KnowledgeFabricMCPTools(
        retrieval_pipeline=pipeline,
        retrieval_store=store,  # type: ignore[arg-type]
        embedding_provider=provider,
        connection_factory=lambda: None,
    )

    result = tools.get_document(document_id=10, tenant_id="team-beta")
    assert result is None, "Wrong-tenant lookup must return None, not leak document data"


def test_vertical_slice_get_document_correct_tenant_returns_document() -> None:
    """get_document with correct tenant_id must return the document dict."""

    class _IsolatingStore:
        def lexical_search(self, *a, **kw): return []

        def vector_search(self, *a, **kw): return []

        def list_sources_for_tenant(self, tenant_id=None): return []

        def get_document(self, *, document_id=None, source_uri=None, tenant_id=None):
            if tenant_id == "team-alpha":
                return {
                    "id": 10,
                    "source_uri": "file://docs/runbook.md",
                    "source_type": "markdown",
                }
            return None

    store = _IsolatingStore()
    provider = MockEmbeddingProvider(_dimension=8)
    pipeline = RetrievalPipeline(retrieval_store=store, embedding_provider=provider)  # type: ignore[arg-type]
    tools = KnowledgeFabricMCPTools(
        retrieval_pipeline=pipeline,
        retrieval_store=store,  # type: ignore[arg-type]
        embedding_provider=provider,
        connection_factory=lambda: None,
    )

    result = tools.get_document(document_id=10, tenant_id="team-alpha")
    assert result is not None
    assert result["id"] == 10
    assert result["source_uri"] == "file://docs/runbook.md"
    assert result["source_type"] == "markdown"
