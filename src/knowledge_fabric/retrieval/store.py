"""Pluggable retrieval store protocol and backend factory."""

from __future__ import annotations

import os
from typing import Any, Protocol

from knowledge_fabric.retrieval.models import RetrievalHit


class RetrievalStore(Protocol):
    """Interface for search stores supporting lexical and vector retrieval."""

    def lexical_search(
        self,
        query_text: str,
        *,
        top_k: int = 10,
        filters: dict[str, object] | None = None,
        tenant_id: str = "default",
    ) -> list[RetrievalHit]:
        """Execute full-text keyword search filtered by tenant."""

    def vector_search(
        self,
        query_vector: list[float],
        *,
        top_k: int = 10,
        filters: dict[str, object] | None = None,
        tenant_id: str = "default",
    ) -> list[RetrievalHit]:
        """Execute dense vector similarity search filtered by tenant."""


def build_retrieval_store(
    backend: str = "",
    connection_factory: Any = None,
) -> RetrievalStore:
    """Instantiate a RetrievalStore based on configuration.

    Supported backends:
      - "postgres" (default) — native PostgreSQL + pgvector + tsvector (zero sprawl)
      - "qdrant" — remote Qdrant cluster via REST API (for 50M+ vector scale)
    """
    selected = (backend or os.environ.get("RETRIEVAL_STORE_BACKEND", "postgres")).lower().strip()

    if selected == "postgres":
        from knowledge_fabric.retrieval.postgres import PostgresRetrievalStore

        if connection_factory is None:
            from knowledge_fabric.config import load_settings
            from knowledge_fabric.db import create_postgres_connection_factory

            settings = load_settings()
            connection_factory = create_postgres_connection_factory(settings.database)

        return PostgresRetrievalStore(connection_factory=connection_factory)

    elif selected == "qdrant":
        from knowledge_fabric.retrieval.qdrant import QdrantRetrievalStore

        url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        collection = os.environ.get("QDRANT_COLLECTION", "knowledge_fabric")
        api_key = os.environ.get("QDRANT_API_KEY", "")
        return QdrantRetrievalStore(url=url, collection=collection, api_key=api_key)

    else:
        raise ValueError(
            f"Unsupported retrieval backend '{selected}'. Must be 'postgres' or 'qdrant'."
        )
