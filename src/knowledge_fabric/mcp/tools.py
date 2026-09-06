"""MCP-style tool surface for Knowledge Fabric retrieval."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from knowledge_fabric.embeddings.providers import EmbeddingProvider
from knowledge_fabric.retrieval.pipeline import RetrievalPipeline
from knowledge_fabric.retrieval.postgres import PostgresRetrievalStore

ConnectionFactory = Callable[[], Any]


class KnowledgeFabricMCPTools:
    """Tool methods matching Phase 1 MCP retrieval contracts."""

    def __init__(
        self,
        *,
        retrieval_pipeline: RetrievalPipeline,
        retrieval_store: PostgresRetrievalStore,
        embedding_provider: EmbeddingProvider | None = None,
        connection_factory: ConnectionFactory | None = None,
    ) -> None:
        self._retrieval_pipeline = retrieval_pipeline
        self._retrieval_store = retrieval_store
        self._embedding_provider = embedding_provider
        self._connection_factory = connection_factory

    def health_check(self) -> dict[str, object]:
        """Return server health and runtime configuration.

        Checks DB connectivity and reports embedding provider details and row counts.
        """
        result: dict[str, object] = {
            "status": "ok",
            "embedding_provider": type(self._embedding_provider).__name__ if self._embedding_provider else "unknown",
            "embedding_dimension": self._embedding_provider.dimension if self._embedding_provider else None,
            "mock_warning": isinstance(self._embedding_provider, _get_mock_provider_type()),
        }

        if self._connection_factory is not None:
            try:
                t0 = time.monotonic()
                conn = self._connection_factory()
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT "
                        "(SELECT COUNT(*) FROM documents) AS doc_count, "
                        "(SELECT COUNT(*) FROM chunks) AS chunk_count, "
                        "(SELECT COUNT(*) FROM audit_events) AS audit_count"
                    )
                    row = cur.fetchone()
                latency_ms = int((time.monotonic() - t0) * 1000)
                if row:
                    result["document_count"] = int(row[0])
                    result["chunk_count"] = int(row[1])
                    result["audit_event_count"] = int(row[2])
                result["db_latency_ms"] = latency_ms
                result["db_status"] = "connected"

                if self._embedding_provider:
                    try:
                        from knowledge_fabric.db.dimension_guard import check_embedding_dimension
                        check_embedding_dimension(
                            conn,
                            provider_dimension=self._embedding_provider.dimension,
                            provider_name=type(self._embedding_provider).__name__,
                        )
                        result["dimension_check"] = "match"
                    except Exception as dim_err:
                        result["dimension_check"] = "mismatch"
                        result["dimension_warning"] = str(dim_err)
            except Exception as exc:
                result["db_status"] = "error"
                result["db_error"] = str(exc)
        else:
            result["db_status"] = "unknown"

        return result

    def list_sources(self) -> dict[str, object]:
        """Return distinct source types and their document counts.

        Allows an AI agent to discover what content domains are available
        before issuing a retrieve_evidence query.
        """
        if self._connection_factory is None:
            return {"sources": [], "error": "No database connection available"}

        try:
            conn = self._connection_factory()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT source_type, COUNT(*) AS doc_count "
                    "FROM documents "
                    "GROUP BY source_type "
                    "ORDER BY doc_count DESC"
                )
                rows = cur.fetchall()
            sources = [
                {"source_type": str(row[0]), "document_count": int(row[1])}
                for row in rows
            ]
            return {"sources": sources, "total_source_types": len(sources)}
        except Exception as exc:
            return {"sources": [], "error": str(exc)}

    def retrieve_evidence(
        self,
        query_text: str,
        top_k: int = 10,
        source_type: str | None = None,
        trace_id: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, object]:
        package = self._retrieval_pipeline.retrieve_evidence(
            query_text=query_text,
            top_k=top_k,
            source_type=source_type,
            trace_id=trace_id,
            tenant_id=tenant_id,
        )
        return package.to_dict()

    def get_document(self, *, document_id: int | None = None, source_uri: str | None = None) -> dict[str, Any] | None:
        return self._retrieval_store.get_document(document_id=document_id, source_uri=source_uri)

    def explain_retrieval(self, query_text: str, top_k: int = 10, source_type: str | None = None) -> dict[str, Any]:
        return self._retrieval_pipeline.explain_retrieval(query_text=query_text, top_k=top_k, source_type=source_type)


def _get_mock_provider_type() -> type:
    """Lazy import to avoid circular dependency in type checks."""
    from knowledge_fabric.embeddings.providers import MockEmbeddingProvider
    return MockEmbeddingProvider
