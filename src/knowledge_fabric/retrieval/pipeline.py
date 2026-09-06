"""End-to-end retrieval orchestration."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from knowledge_fabric.db.audit import AuditLogger
from knowledge_fabric.embeddings import EmbeddingProvider
from knowledge_fabric.evidence.models import EvidencePackage, build_evidence_package
from knowledge_fabric.fusion import reciprocal_rank_fusion
from knowledge_fabric.reranking import PassthroughReranker, Reranker
from knowledge_fabric.retrieval.store import RetrievalStore


@dataclass(slots=True)
class RetrievalTrace:
    """Debug and observability details for one retrieval call."""

    query_text: str
    top_k: int
    lexical_count: int
    vector_count: int
    fused_count: int
    latency_ms: int


_DEFAULT_MAX_QUERY_LENGTH = int(os.environ.get("KNOWLEDGE_MAX_QUERY_LENGTH", "4000"))
_DEFAULT_MAX_TOP_K = int(os.environ.get("KNOWLEDGE_MAX_TOP_K", "100"))
_DEFAULT_MAX_RERANK_CANDIDATES = int(os.environ.get("KNOWLEDGE_MAX_RERANK_CANDIDATES", "100"))

# Supports standard enterprise formats: alphanumeric, hyphens, underscores, dots, colons, and @ (emails, domains, URNs, UUIDs)
_TENANT_ID_REGEX = re.compile(r"^[a-zA-Z0-9_.:@-]{1,128}$")


def validate_tenant_id(tenant_id: str | None) -> str | None:
    """Validate that tenant_id adheres to safe enterprise namespace format.

    Supports UUIDs, domain names, emails, and namespaced IDs while preventing
    SQL injection, path traversal (e.g. '../'), and control character injection.
    Can be bypassed if KNOWLEDGE_STRICT_TENANT_CHECK=false.
    """
    if tenant_id is None:
        return None
    cleaned = tenant_id.strip()
    if not cleaned:
        return None

    # Allow disabling strict check via environment if custom enterprise naming schemes are used
    if os.environ.get("KNOWLEDGE_STRICT_TENANT_CHECK", "true").lower() in ("false", "0", "off"):
        # Still sanitize against null bytes and control chars
        return "".join(ch for ch in cleaned if ord(ch) >= 32 and ch != "\x7f")[:128]

    if not _TENANT_ID_REGEX.match(cleaned) or ".." in cleaned:
        raise ValueError(f"Invalid tenant_id format: '{tenant_id!r}'. Must match ^[a-zA-Z0-9_.:@-]{{1,128}}$ with no path traversal.")
    return cleaned


class RetrievalPipeline:
    """Coordinates lexical/vector retrieval, fusion, packaging, and audit logging."""

    def __init__(
        self,
        *,
        retrieval_store: RetrievalStore,
        embedding_provider: EmbeddingProvider,
        audit_logger: AuditLogger | None = None,
        reranker: Reranker | None = None,
        rrf_k: int = 60,
        lexical_weight: float = 1.0,
        vector_weight: float = 1.0,
        max_query_length: int | None = None,
        max_top_k: int | None = None,
        max_rerank_candidates: int | None = None,
    ) -> None:
        self._retrieval_store = retrieval_store
        self._embedding_provider = embedding_provider
        self._audit_logger = audit_logger
        self._reranker: Reranker = reranker if reranker is not None else PassthroughReranker()
        self._rrf_k = rrf_k
        self._lexical_weight = lexical_weight
        self._vector_weight = vector_weight
        self._max_query_length = max_query_length if max_query_length is not None else _DEFAULT_MAX_QUERY_LENGTH
        self._max_top_k = max_top_k if max_top_k is not None else _DEFAULT_MAX_TOP_K
        self._max_rerank_candidates = max_rerank_candidates if max_rerank_candidates is not None else _DEFAULT_MAX_RERANK_CANDIDATES

    def retrieve_evidence(
        self,
        *,
        query_text: str,
        top_k: int = 10,
        source_type: str | None = None,
        trace_id: str | None = None,
        tenant_id: str | None = None,
    ) -> EvidencePackage:
        package, _ = self.retrieve_with_trace(
            query_text=query_text,
            top_k=top_k,
            source_type=source_type,
            trace_id=trace_id,
            tenant_id=tenant_id,
        )
        return package

    def retrieve_with_trace(
        self,
        *,
        query_text: str,
        top_k: int = 10,
        source_type: str | None = None,
        trace_id: str | None = None,
        tenant_id: str | None = None,
    ) -> tuple[EvidencePackage, RetrievalTrace]:
        # Security hardening: Configurable input bounding against DoS & Injection
        safe_query = (query_text or "").strip()[:self._max_query_length]
        safe_top_k = max(1, min(top_k, self._max_top_k))
        safe_tenant = validate_tenant_id(tenant_id)

        start = perf_counter()
        lexical = self._retrieval_store.lexical_search(
            safe_query, top_k=safe_top_k, source_type=source_type, tenant_id=safe_tenant
        )
        vector_query = self._embedding_provider.embed_texts([safe_query])[0]
        vector = self._retrieval_store.vector_search(
            vector_query, top_k=safe_top_k, source_type=source_type, tenant_id=safe_tenant
        )

        fused = reciprocal_rank_fusion(
            lexical_hits=lexical,
            vector_hits=vector,
            k=self._rrf_k,
            lexical_weight=self._lexical_weight,
            vector_weight=self._vector_weight,
        )
        # Cap candidate pool for reranking to protect CPU/GPU from compute explosion
        candidates_to_rerank = fused[:self._max_rerank_candidates]
        # Apply reranker (no-op if PassthroughReranker)
        reranked = self._reranker.rerank(safe_query, candidates_to_rerank, top_n=safe_top_k)
        package = build_evidence_package(safe_query, reranked)
        latency_ms = int((perf_counter() - start) * 1000)

        trace = RetrievalTrace(
            query_text=safe_query,
            top_k=safe_top_k,
            lexical_count=len(lexical),
            vector_count=len(vector),
            fused_count=len(reranked),
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
