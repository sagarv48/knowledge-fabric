"""End-to-end retrieval orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from knowledge_fabric.db.audit import AuditLogger
from knowledge_fabric.embeddings import EmbeddingProvider
from knowledge_fabric.evidence.models import EvidencePackage, build_evidence_package
from knowledge_fabric.fusion import reciprocal_rank_fusion
from knowledge_fabric.retrieval.postgres import PostgresRetrievalStore


@dataclass(slots=True)
class RetrievalTrace:
    """Debug and observability details for one retrieval call."""

    query_text: str
    top_k: int
    lexical_count: int
    vector_count: int
    fused_count: int
    latency_ms: int


class RetrievalPipeline:
    """Coordinates lexical/vector retrieval, fusion, packaging, and audit logging."""

    def __init__(
        self,
        *,
        retrieval_store: PostgresRetrievalStore,
        embedding_provider: EmbeddingProvider,
        audit_logger: AuditLogger | None = None,
        rrf_k: int = 60,
        lexical_weight: float = 1.0,
        vector_weight: float = 1.0,
    ) -> None:
        self._retrieval_store = retrieval_store
        self._embedding_provider = embedding_provider
        self._audit_logger = audit_logger
        self._rrf_k = rrf_k
        self._lexical_weight = lexical_weight
        self._vector_weight = vector_weight

    def retrieve_evidence(
        self,
        *,
        query_text: str,
        top_k: int = 10,
        source_type: str | None = None,
        trace_id: str | None = None,
    ) -> EvidencePackage:
        package, _ = self.retrieve_with_trace(
            query_text=query_text,
            top_k=top_k,
            source_type=source_type,
            trace_id=trace_id,
        )
        return package

    def retrieve_with_trace(
        self,
        *,
        query_text: str,
        top_k: int = 10,
        source_type: str | None = None,
        trace_id: str | None = None,
    ) -> tuple[EvidencePackage, RetrievalTrace]:
        start = perf_counter()
        lexical = self._retrieval_store.lexical_search(query_text, top_k=top_k, source_type=source_type)
        vector_query = self._embedding_provider.embed_texts([query_text])[0]
        vector = self._retrieval_store.vector_search(vector_query, top_k=top_k, source_type=source_type)

        fused = reciprocal_rank_fusion(
            lexical_hits=lexical,
            vector_hits=vector,
            k=self._rrf_k,
            lexical_weight=self._lexical_weight,
            vector_weight=self._vector_weight,
        )
        fused = fused[:top_k]
        package = build_evidence_package(query_text, fused)
        latency_ms = int((perf_counter() - start) * 1000)

        trace = RetrievalTrace(
            query_text=query_text,
            top_k=top_k,
            lexical_count=len(lexical),
            vector_count=len(vector),
            fused_count=len(fused),
            latency_ms=latency_ms,
        )

        if self._audit_logger is not None:
            self._audit_logger.log_retrieval(
                query_text=query_text,
                top_k=top_k,
                retrieval_mode="hybrid_rrf",
                result_count=len(fused),
                latency_ms=latency_ms,
                trace_id=trace_id,
                details=self._trace_to_dict(trace),
            )
        return package, trace

    def explain_retrieval(
        self,
        *,
        query_text: str,
        top_k: int = 10,
        source_type: str | None = None,
    ) -> dict[str, Any]:
        package, trace = self.retrieve_with_trace(query_text=query_text, top_k=top_k, source_type=source_type)
        return {
            "query_text": query_text,
            "top_k": top_k,
            "trace": self._trace_to_dict(trace),
            "result_chunk_ids": [item.chunk_id for item in package.items],
            "sources": package.retrieval_summary.get("sources", []),
        }

    @staticmethod
    def _trace_to_dict(trace: RetrievalTrace) -> dict[str, Any]:
        return {
            "query_text": trace.query_text,
            "top_k": trace.top_k,
            "lexical_count": trace.lexical_count,
            "vector_count": trace.vector_count,
            "fused_count": trace.fused_count,
            "latency_ms": trace.latency_ms,
        }
