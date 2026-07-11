"""MCP-style tool surface for Knowledge Fabric retrieval."""

from __future__ import annotations

from typing import Any

from knowledge_fabric.retrieval.pipeline import RetrievalPipeline
from knowledge_fabric.retrieval.postgres import PostgresRetrievalStore


class KnowledgeFabricMCPTools:
    """Tool methods matching Phase 1 MCP retrieval contracts."""

    def __init__(self, *, retrieval_pipeline: RetrievalPipeline, retrieval_store: PostgresRetrievalStore) -> None:
        self._retrieval_pipeline = retrieval_pipeline
        self._retrieval_store = retrieval_store

    def retrieve_evidence(
        self,
        query_text: str,
        top_k: int = 10,
        source_type: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, object]:
        package = self._retrieval_pipeline.retrieve_evidence(
            query_text=query_text,
            top_k=top_k,
            source_type=source_type,
            trace_id=trace_id,
        )
        return package.to_dict()

    def get_document(self, *, document_id: int | None = None, source_uri: str | None = None) -> dict[str, Any] | None:
        return self._retrieval_store.get_document(document_id=document_id, source_uri=source_uri)

    def explain_retrieval(self, query_text: str, top_k: int = 10, source_type: str | None = None) -> dict[str, Any]:
        return self._retrieval_pipeline.explain_retrieval(query_text=query_text, top_k=top_k, source_type=source_type)
