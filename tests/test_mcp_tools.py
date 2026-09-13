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
    def get_document(
        *,
        document_id: int | None = None,
        source_uri: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, object]:
        return {"id": document_id or 1, "source_uri": source_uri or "memory://doc", "tenant_id": tenant_id}

    @staticmethod
    def list_sources_for_tenant(tenant_id: str | None = None) -> list[tuple]:
        return [("markdown", 2)]


def test_mcp_tools_surface() -> None:
    tools = KnowledgeFabricMCPTools(
        retrieval_pipeline=_FakePipeline(),  # type: ignore[arg-type]
        retrieval_store=_FakeStore(),  # type: ignore[arg-type]
    )

    evidence = tools.retrieve_evidence("query")
    document = tools.get_document(document_id=5, tenant_id="team-alpha")
    explanation = tools.explain_retrieval("query")
    sources = tools.list_sources(tenant_id="team-alpha")

    assert evidence["query_text"] == "query"
    assert document["id"] == 5
    assert document["tenant_id"] == "team-alpha"
    assert explanation["trace"]["fused_count"] == 1
    assert sources["sources"][0]["source_type"] == "markdown"


def test_mcp_tools_get_document_passes_tenant_id() -> None:
    """Verify tenant_id is forwarded to the store (cross-tenant isolation)."""
    received: dict[str, object] = {}

    class _TrackingStore:
        @staticmethod
        def get_document(*, document_id=None, source_uri=None, tenant_id=None):
            received["tenant_id"] = tenant_id
            return None  # simulate cross-tenant miss

        @staticmethod
        def list_sources_for_tenant(tenant_id=None):
            return []

    tools = KnowledgeFabricMCPTools(
        retrieval_pipeline=_FakePipeline(),  # type: ignore[arg-type]
        retrieval_store=_TrackingStore(),  # type: ignore[arg-type]
    )
    result = tools.get_document(document_id=99, tenant_id="team-beta")
    assert result is None
    assert received["tenant_id"] == "team-beta"

