"""MCP server entrypoint for Knowledge Fabric tools."""

from __future__ import annotations

import os
from typing import Any

from knowledge_fabric.config import Settings, load_settings
from knowledge_fabric.db import AuditLogger, create_postgres_connection_factory
from knowledge_fabric.embeddings import build_embedding_provider
from knowledge_fabric.mcp.tools import KnowledgeFabricMCPTools
from knowledge_fabric.retrieval.pipeline import RetrievalPipeline
from knowledge_fabric.retrieval.postgres import PostgresRetrievalStore


def build_tools_from_settings(settings: Settings) -> KnowledgeFabricMCPTools:
    """Build MCP tools with configured retrieval dependencies."""
    connection_factory = create_postgres_connection_factory(settings.database)
    retrieval_store = PostgresRetrievalStore(connection_factory=connection_factory)
    embedding_provider = build_embedding_provider(
        provider_name=settings.embeddings.provider,
        dimension=settings.embeddings.dimension,
    )
    audit_logger = AuditLogger(connection_factory=connection_factory)
    pipeline = RetrievalPipeline(
        retrieval_store=retrieval_store,
        embedding_provider=embedding_provider,
        audit_logger=audit_logger,
        rrf_k=settings.retrieval.rrf_k,
        lexical_weight=settings.retrieval.lexical_weight,
        vector_weight=settings.retrieval.vector_weight,
    )
    return KnowledgeFabricMCPTools(
        retrieval_pipeline=pipeline,
        retrieval_store=retrieval_store,
        embedding_provider=embedding_provider,
        connection_factory=connection_factory,
    )


def create_mcp_server(tools: KnowledgeFabricMCPTools) -> Any:
    """Create MCP server with retrieval tool registration."""
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("knowledge-fabric")

    @server.tool(name="health_check")
    def health_check() -> dict[str, object]:
        """Check server health and return runtime configuration.

        Returns embedding provider name and dimension, DB connectivity status,
        and approximate document/chunk counts. Useful for AI agents to orient
        themselves before querying.
        """
        return tools.health_check()

    @server.tool(name="list_sources")
    def list_sources() -> dict[str, object]:
        """List all ingested source types and their document counts.

        Returns distinct source_type values with document counts so an AI agent
        can discover what content domains are available before issuing a query.
        Use source_type as a filter in retrieve_evidence to scope retrieval.
        """
        return tools.list_sources()

    @server.tool(name="retrieve_evidence")
    def retrieve_evidence(
        query_text: str,
        top_k: int = 10,
        source_type: str | None = None,
        trace_id: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, object]:
        # tenant_id from the call argument takes priority;
        # fall back to server-level default from environment.
        effective_tenant = tenant_id or os.environ.get("KF_DEFAULT_TENANT") or None
        return tools.retrieve_evidence(
            query_text=query_text,
            top_k=top_k,
            source_type=source_type,
            trace_id=trace_id,
            tenant_id=effective_tenant,
        )

    @server.tool(name="get_document")
    def get_document(
        document_id: int | None = None,
        source_uri: str | None = None,
    ) -> dict[str, object] | None:
        return tools.get_document(document_id=document_id, source_uri=source_uri)

    @server.tool(name="explain_retrieval")
    def explain_retrieval(
        query_text: str,
        top_k: int = 10,
        source_type: str | None = None,
    ) -> dict[str, object]:
        return tools.explain_retrieval(query_text=query_text, top_k=top_k, source_type=source_type)

    return server


def run_mcp_server(settings_path: str = "config/settings.yaml") -> None:
    """Run the MCP server using stdio transport."""
    settings = load_settings(settings_path)
    tools = build_tools_from_settings(settings)
    server = create_mcp_server(tools)
    server.run()
