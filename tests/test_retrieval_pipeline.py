from __future__ import annotations

from knowledge_fabric.embeddings import MockEmbeddingProvider
from knowledge_fabric.retrieval import RetrievalHit
from knowledge_fabric.retrieval.pipeline import RetrievalPipeline


class _FakeStore:
    def lexical_search(
        self,
        query_text: str,
        top_k: int = 10,
        source_type: str | None = None,
        tenant_id: str | None = None,
        **kwargs: object,
    ) -> list[RetrievalHit]:
        return [
            RetrievalHit(
                chunk_id=1,
                document_id=10,
                document_uri="memory://doc-10",
                chunk_index=0,
                chunk_text="lexical result",
                score=0.8,
                source="lexical",
                metadata={"kind": "lexical"},
            )
        ]

    def vector_search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        source_type: str | None = None,
        tenant_id: str | None = None,
        **kwargs: object,
    ) -> list[RetrievalHit]:
        return [
            RetrievalHit(
                chunk_id=2,
                document_id=11,
                document_uri="memory://doc-11",
                chunk_index=1,
                chunk_text="vector result",
                score=0.7,
                source="vector",
                metadata={"kind": "vector"},
            )
        ]


class _FakeAuditLogger:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def log_retrieval(self, **kwargs: object) -> None:
        self.calls.append(kwargs)


def test_pipeline_retrieves_and_logs() -> None:
    audit = _FakeAuditLogger()
    pipeline = RetrievalPipeline(
        retrieval_store=_FakeStore(),  # type: ignore[arg-type]
        embedding_provider=MockEmbeddingProvider(_dimension=8),
        audit_logger=audit,  # type: ignore[arg-type]
    )

    package, trace = pipeline.retrieve_with_trace(query_text="test query", top_k=5, trace_id="trace-1")

    assert package.query_text == "test query"
    assert len(package.items) == 2
    assert trace.fused_count == 2
    assert len(audit.calls) == 1
    assert audit.calls[0]["trace_id"] == "trace-1"


def test_pipeline_explain_retrieval() -> None:
    pipeline = RetrievalPipeline(
        retrieval_store=_FakeStore(),  # type: ignore[arg-type]
        embedding_provider=MockEmbeddingProvider(_dimension=8),
    )

    details = pipeline.explain_retrieval(query_text="security", top_k=3)

    assert details["query_text"] == "security"
    assert details["top_k"] == 3
    assert details["trace"]["lexical_count"] == 1
    assert set(details["sources"]) == {"lexical", "vector"}
