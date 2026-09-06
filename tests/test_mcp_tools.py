from __future__ import annotations

from knowledge_fabric.mcp import KnowledgeFabricMCPTools


class _FakePipeline:
    def retrieve_evidence(
        self,
        *,
        query_text: str,
        top_k: int = 10,
        source_type: str | None = None,
        trace_id: str | None = None,
        tenant_id: str | None = None,
        **kwargs: object,
    ):
        class _Package:
            @staticmethod
            def to_dict() -> dict[str, object]:
                return {"query_text": query_text, "items": [{"chunk_id": 1}]}

        return _Package()

    @staticmethod
    def explain_retrieval(
        query_text: str,
        top_k: int = 10,
        source_type: str | None = None,
        tenant_id: str | None = None,
        **kwargs: object,
    ) -> dict[str, object]:
        return {"query_text": query_text, "top_k": top_k, "trace": {"fused_count": 1}}


class _FakeStore:
    @staticmethod
    def get_document(*, document_id: int | None = None, source_uri: str | None = None) -> dict[str, object]:
        return {"id": document_id or 1, "source_uri": source_uri or "memory://doc"}


def test_mcp_tools_surface() -> None:
    tools = KnowledgeFabricMCPTools(
        retrieval_pipeline=_FakePipeline(),  # type: ignore[arg-type]
        retrieval_store=_FakeStore(),  # type: ignore[arg-type]
    )

    evidence = tools.retrieve_evidence("query")
    document = tools.get_document(document_id=5)
    explanation = tools.explain_retrieval("query")

    assert evidence["query_text"] == "query"
    assert document["id"] == 5
    assert explanation["trace"]["fused_count"] == 1
