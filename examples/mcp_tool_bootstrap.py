"""Example bootstrap for Knowledge Fabric MCP tools."""

from __future__ import annotations

from knowledge_fabric.db import AuditLogger
from knowledge_fabric.embeddings import MockEmbeddingProvider
from knowledge_fabric.mcp import KnowledgeFabricMCPTools
from knowledge_fabric.retrieval.pipeline import RetrievalPipeline
from knowledge_fabric.retrieval.postgres import PostgresRetrievalStore


def build_tools(connection_factory):
    retrieval_store = PostgresRetrievalStore(connection_factory=connection_factory)
    pipeline = RetrievalPipeline(
        retrieval_store=retrieval_store,
        embedding_provider=MockEmbeddingProvider(_dimension=1536),
        audit_logger=AuditLogger(connection_factory=connection_factory),
        rrf_k=60,
        lexical_weight=1.0,
        vector_weight=1.0,
    )
    return KnowledgeFabricMCPTools(retrieval_pipeline=pipeline, retrieval_store=retrieval_store)
